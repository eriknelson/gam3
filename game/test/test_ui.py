
"""
Tests for L{game.ui}.
"""

from twisted.trial.unittest import TestCase
from twisted.test.proto_helpers import StringTransport
from twisted.internet.protocol import ClientFactory, Protocol
from twisted.internet.defer import succeed

from game.network import NetworkController
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
        self.ui = UI(self.reactor, windowFactory=FakeWindow)


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
        self.assertEqual(protocol.scheduler, self.reactor.callLater)


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
        create a L{Window} and call L{Window.go} on it.
        """
        environment = object()
        self.ui.gotIntroduced(environment)
        self.assertIdentical(self.ui.window.environment, environment)
        self.assertIdentical(self.ui.window.scheduler, self.reactor)
        self.assertEqual(self.ui.window.went, [True])

    # XXX gotIntroduced returns a Deferred maybe?


    def callRemote(self, commandType, **kw):
        """
        Record an attempt to invoke a remote command.
        """
        result = Deferred()
        self.calls.append((result, commandType, kw))
        return result



class FakeWindow(object):
    """
    A thing that is looks like L{game.view.Window}.

    @ivar environment: The first argument to the initializer.
    @ivar scheduler: The second argument to the initializer.
    """

    def __init__(self, environment, scheduler):
        self.environment = environment
        self.scheduler = scheduler
        self.went = []


    def go(self):
        """
        Don't do anything.
        """
        self.went.append(True)
