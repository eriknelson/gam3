# -*- test-case-name: game.test.test_ui -*-

"""
Combination of View and Controller (maybe the Model is hiding in there too).
"""

from twisted.internet.protocol import ClientFactory
from twisted.protocols.policies import ProtocolWrapper, WrappingFactory
from twisted.internet.defer import Deferred
from twisted.internet import reactor

from game.network import NetworkController
from game.view import Window
from game.controller import PlayerController


class ConnectionNotificationWrapper(ProtocolWrapper):
    """
    A protocol wrapper which fires a Deferred when the connection is made.
    """

    def makeConnection(self, transport):
        """
        Fire the Deferred at C{self.factory.connectionNotification} with the
        real protocol.
        """
        ProtocolWrapper.makeConnection(self, transport)
        self.factory.connectionNotification.callback(self.wrappedProtocol)



class ConnectionNotificationFactory(WrappingFactory):
    """
    A factory which uses L{ConnectionNotificationWrapper}.

    @ivar connectionNotification: The Deferred which will be fired with a
    Protocol at some point.
    """
    protocol = ConnectionNotificationWrapper

    def __init__(self, realFactory):
        WrappingFactory.__init__(self, realFactory)
        self.connectionNotification = Deferred()



class UI(object):
    """
    See L{game.ui}.

    @ivar reactor: Something which provides
        L{twisted.internet.interfaces.IReactorTCP} and
        L{twisted.internet.interfaces.IReactorTime}.

    @ivar windowFactory: The factory that should produce things like
        L{game.view.Window}.
    """

    def __init__(self, reactor=reactor, windowFactory=Window):
        self.reactor = reactor
        self.windowFactory = windowFactory


    def connect(self, (host, port)):
        """
        Connect to the Game server at the given (host, port).

        @param host: The name of the host to connect to.
        @param port: The TCP port number to connect to.
        """
        clientFactory = ClientFactory()
        clientFactory.protocol = lambda: NetworkController(
            self.reactor)
        factory = ConnectionNotificationFactory(clientFactory)
        self.reactor.connectTCP(host, port, factory)
        return factory.connectionNotification


    def gotInitialPlayer(self, player):
        """
        Hook up a L{PlayerView} and a L{PlayerController} for the
        given L{Player}.
        """
        # XXX Do something with the view!
        self.window.submitTo(PlayerController(player))


    def gotIntroduced(self, environment):
        """
        Hook up a user-interface controller for the L{Player} and display the
        L{Environment} in a L{Window}.
        """
        self.window = self.windowFactory(environment, self.reactor)
        player = environment.initialPlayer
        if player is not None:
            self.gotInitialPlayer(player)
        environment.start()
        return self.window.go()


    def start(self, (host, port)):
        """
        Let's Go!

        - Connect to the given host and port.
        - Make introductions.
        - Run a GUI.
        """
        d = self.connect((host, port))
        d.addCallback(lambda protocol: protocol.introduce())
        d.addCallback(self.gotIntroduced)
        return d
