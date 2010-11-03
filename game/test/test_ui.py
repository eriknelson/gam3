
"""
Tests for L{game.ui}.
"""

from twisted.trial.unittest import TestCase
from twisted.test.proto_helpers import StringTransport
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet.defer import succeed
from twisted.internet.task import Clock

from game.view import Scene, TerrainView, loadImage
from game.controller import PlayerController
from game.network import NetworkController
from game.environment import Environment
from game.ui import (UI, ConnectionNotificationFactory,
                     ConnectionNotificationWrapper)


class StubReactor(object):
    """
    A fake reactor which records stuff.

    @ivar tcpConnectionAttempts: List of tuples of (host, port, factory).
    """

    def __init__(self):
        self.tcpConnectionAttempts = []


    def connectTCP(self, host, port, factory):
        """
        Record an attempt to connect to a TCP host. Add (host, port, factory)
        to C{self.tcpConnectionAttempts}.
        """
        self.tcpConnectionAttempts.append((host, port, factory))


    def callLater(self, seconds, function, *args, **kwargs):
        """
        Return None.
        """



class StubWindow(object):
    """
    A thing that is looks like L{game.view.Window}.

    @ivar environment: The first argument to the initializer.
    @ivar clock: The second argument to the initializer.
    @ivar controller: The controller being submitted to.
    """

    def __init__(self, environment, clock):
        self.environment = environment
        self.clock = clock
        self.went = []
        self.controller = None
        self.scene = Scene()


    def submitTo(self, controller):
        """
        Set C{self.controller}.
        """
        self.controller = controller


    def go(self):
        """
        Append C{True} to C{self.went}.
        """
        self.went.append(True)



class ConnectionNotificationWrapperTests(TestCase):
    """
    Tests for L{ConnectionNotificationWrapper}.
    """

    def test_makeConnectionFiresDeferredWithProtocol(self):
        """
        When L{ConnectionNotificationWrapper.makeConnection} is called, the
        Deferred previously registered should be fired with the protocol
        instance.
        """
        realFactory = ClientFactory()
        realProtocol = Protocol()
        realFactory.protocol = lambda: realProtocol

        wrappedFactory = ConnectionNotificationFactory(realFactory)
        wrappedProtocol = wrappedFactory.buildProtocol(None)
        wrappedProtocol.makeConnection(StringTransport())
        wrappedFactory.connectionNotification.addCallback(
            self.assertIdentical, realProtocol)
        return wrappedFactory.connectionNotification


    def test_makeConnectionUpcalls(self):
        """
        L{ConnectionNotificationWrapper.makeConnection} should upcall.
        """
        realProtocol = Protocol()
        transport = StringTransport()
        wrappedProtocol = ConnectionNotificationWrapper(
            ConnectionNotificationFactory(ClientFactory()), realProtocol)
        wrappedProtocol.makeConnection(transport)
        self.assertIdentical(wrappedProtocol.transport, transport)
        self.assertIdentical(realProtocol.transport, wrappedProtocol)

#     def test_makeConnectionErrorsDeferredWithProtocol(self):
#     def test_connectionNotificationDeferredGetsNewValueOfSomeSortAfterResult(self):



class UITests(TestCase):
    """
    Tests for L{UI}.
    """

    def setUp(self):
        self.host = 'example.com'
        self.port = 12345
        self.reactor = StubReactor()
        self.ui = UI(self.reactor, windowFactory=StubWindow)

    def test_defaults(self):
        """
        Instantiating a L{UI} with no arguments should work and should
        use appropriate default values for the C{reactor} and
        C{windowFactory}.
        """
        from twisted.internet import reactor
        from game.view import Window
        ui = UI()
        self.assertIdentical(ui.reactor, reactor)
        self.assertIdentical(ui.windowFactory, Window)


    def test_connect(self):
        """
        L{UI.connect} should I{connect} to the Game Server on the given (host,
        port) TUPLE (XXX use an endpoint).
        """
        self.ui.connect((self.host, self.port))
        [(listenedHost,
          listenedPort,
          factory)] = self.reactor.tcpConnectionAttempts
        self.assertEqual(listenedHost, self.host)
        self.assertEqual(listenedPort, self.port)
        protocol = factory.buildProtocol((self.host, self.port)
                                         ).wrappedProtocol
        self.assertTrue(isinstance(protocol, NetworkController))
        self.assertEqual(protocol.environment, None)
        self.assertEqual(protocol.clock, self.reactor)


    def test_connectionSuccessFiresDeferred(self):
        """
        When Twisted tells the factory to build a protocol and then tells the
        protocol that the connection is made, the Deferred that L{UI.connect}
        returns should fire with the L{NetworkController} instance.
        """

        def gotProtocol(protocolWhatWasGot):
            """
            Wrapping is bad for you.
            """
            self.assertIdentical(protocolWhatWasGot, protocol.wrappedProtocol)
            self.assertIdentical(protocolWhatWasGot.transport, protocol)

        d = self.ui.connect((self.host, self.port))
        d.addCallback(gotProtocol)
        factory = self.reactor.tcpConnectionAttempts[0][2]
        protocol = factory.buildProtocol((self.host, self.port))
        protocol.makeConnection(StringTransport())
        return d


    def test_start(self):
        """
        L{UI.start} should connect to the game server, introduce
        itself, and create a Window with the environment when the
        introduction is reciprocated.
        """
        class Introducable(object):
            """
            Thing which records L{introduce} calls.

            @ivar introductions: list of True.
            @ivar environment: Some object.
            """

            def __init__(self):
                self.introductions = []
                self.environment = object()

            def introduce(self):
                """
                Record the fact that an introduction was attempted.
                """
                self.introductions.append(True)
                return self.environment

        environments = []
        introducable = Introducable()
        connections = {(self.host, self.port): succeed(introducable)}
        self.ui.connect = connections.pop
        self.ui.gotIntroduced = environments.append
        self.ui.start((self.host, self.port))
        self.assertEqual(introducable.introductions, [True])
        self.assertEqual(environments, [introducable.environment])


    def test_gotIntroduced(self):
        """
        When the introduction has been reciprocated, the L{UI} should
        start the Environment and create a L{Window} and call
        L{Window.go} on it.
        """
        starts = []
        environment = Environment(3, None)
        environment.start = lambda: starts.append(True)
        self.ui.gotIntroduced(environment)
        self.assertIdentical(self.ui.window.environment, environment)
        self.assertIdentical(self.ui.window.clock, self.reactor)
        self.assertEqual(self.ui.window.went, [True])
        self.assertEqual(starts, [True])


    def test_gotIntroducedWithInitialPlayer(self):
        """
        The initial L{Player} in the L{Environment} should be passed
        to L{UI.gotInitialPlayer}.
        """
        player = object()
        environment = Environment(10, Clock())
        environment.setInitialPlayer(player)
        initialEvents = []
        def gotInitialPlayer(player):
            initialEvents.append(('player', player))
        def gotTerrain(terrain):
            initialEvents.append(('terrain', terrain))
        self.ui.gotInitialPlayer = gotInitialPlayer
        self.ui.gotTerrain = gotTerrain
        self.ui.gotIntroduced(environment)
        self.assertEqual(initialEvents, [('terrain', environment.terrain),
                                         ('player', player)])


    def test_gotInitialPlayer(self):
        """
        After L{UI.gotInitialPlayer}, that player should have a view
        in and a controller on the window.
        """
        player = object()
        window = self.ui.window = StubWindow(None, None)
        self.ui.gotInitialPlayer(player)
        # XXX The view needs to do something, maybe.
        self.assertTrue(
            isinstance(window.controller, PlayerController))
        self.assertIdentical(window.controller.player, player)


    def test_gotTerrain(self):
        """
        L{UI.gotTerrain} should pass the terrain it receives on to its
        environment.
        """
        terrain = object()
        window = self.ui.window = StubWindow(None, None)
        self.ui.environment = Environment(10, Clock())
        self.ui.gotTerrain(terrain)
        [view] = window.scene._items
        self.assertTrue(isinstance(view, TerrainView))
        self.assertIdentical(view.terrain, terrain)
        self.assertIdentical(view.loader, loadImage)


    def test_noInitialPlayer(self):
        """
        If no initial L{Player} is available in the L{Environment}, no view or
        controller should be created.
        """
        environment = Environment(10, Clock())
        initialPlayers = []
        self.ui.gotInitialPlayer = initialPlayers.append
        self.ui.gotIntroduced(environment)
        self.assertEqual(len(initialPlayers), 0)
        self.assertIdentical(self.ui.window.controller, None)
