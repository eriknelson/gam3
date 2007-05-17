
"""
Tests for L{game.ui}.
"""

from twisted.trial.unittest import TestCase
from twisted.test.proto_helpers import StringTransport
from twisted.internet.defer import Deferred
from twisted.internet.protocol import ClientFactory, Protocol

from game.network import NetworkController
from game.ui import UI, ConnectionNotificationFactory, ConnectionNotificationWrapper


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
    def test_connect(self):
        """
        L{UI.connect} should I{connect} to the Game Server on the given (host,
        port) TUPLE (XXX use an endpoint).
        """
        host = 'example.com'
        port = 12345
        reactor = StubReactor()
        UI(reactor).connect((host, port))
        [(listenedHost, listenedPort, factory)] = reactor.tcpConnectionAttempts
        self.assertEqual(listenedHost, host)
        self.assertEqual(listenedPort, port)
        protocol = factory.buildProtocol((host, port)).wrappedProtocol
        self.assertTrue(isinstance(protocol, NetworkController))
        self.assertEqual(protocol.environment, None)
        self.assertEqual(protocol.scheduler, reactor.callLater)


    def test_connectionSuccessFiresDeferred(self):
        """
        When Twisted tells the factory to build a protocol and then tells the
        protocol that the connection is made, the Deferred that L{UI.connect}
        returns should fire with the L{NetworkController} instance.
        """
        host = 'example.com'
        port = 12345
        reactor = StubReactor()

        def gotProtocol(protocolWhatWasGot):
            """
            Wrapping is bad for you.
            """
            self.assertIdentical(protocolWhatWasGot, protocol.wrappedProtocol)
            self.assertIdentical(protocolWhatWasGot.transport, protocol)

        d = UI(reactor).connect((host, port))
        d.addCallback(gotProtocol)
        factory = reactor.tcpConnectionAttempts[0][2]
        protocol = factory.buildProtocol((host, port))
        protocol.makeConnection(StringTransport())
        return d
