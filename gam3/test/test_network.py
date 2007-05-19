"""
Tests for the networking functionality of Gam3.
"""

from zope.interface.verify import verifyObject

from twisted.trial.unittest import TestCase
from twisted.internet.interfaces import IProtocolFactory

from game.network import Introduce
from game.player import Player

from gam3.network import Gam3Factory, Gam3Server



class FakeWorld(object):
    """
    Act like a FORWARD RESOLUTION:L{World}.

    @ivar players: L{Player}s that have been created.
    """
    identifier = 1
    granularity = 7
    speed = 3
    x = 129
    y = -299999

    def __init__(self):
        self.players = []

    def createPlayer(self):
        """
        Create a L{Player}, recording it in C{self.players}.
        """
        self.players.append(Player((self.x, self.y), self.speed, lambda: 3))
        return self.players[-1]



class NetworkTests(TestCase):
    """
    Tests for the client-facing AMP server protocol.
    """

    def test_introduction(self):
        """
        The server should respond to L{Introduce} commands with
        environment parameters and new player's data.
        """
        world = FakeWorld()
        protocol = Gam3Server(world)
        responder = protocol.lookupFunction(Introduce.commandName)
        d = responder({})

        def gotResult(box):
            self.assertEqual(len(world.players), 1)
            identifier = protocol.identifierForPlayer(world.players[0])
            self.assertEqual(box,
                             {'identifier': str(identifier),
                              'granularity': str(world.granularity),
                              'speed': str(world.speed),
                              'x': str(world.x),
                              'y': str(world.y)})

        d.addCallback(gotResult)
        return d


    def test_identifierForPlayer(self):
        """
        L{Gam3Server} should provide an identifier producing function
        which produces identifiers that go up.
        """
        protocol = Gam3Server(None)
        player1 = object()
        player2 = object()
        playerOneID = protocol.identifierForPlayer(player1)
        playerTwoID = protocol.identifierForPlayer(player2)
        self.assertEqual(protocol.identifierForPlayer(player1), playerOneID)
        self.assertEqual(protocol.identifierForPlayer(player2), playerTwoID)
        self.assertNotEqual(playerOneID, playerTwoID)



class FactoryTests(TestCase):
    """
    Tests for L{Gam3Factory}.
    """
    def test_world(self):
        """
        L{Gam3Factory.buildProtocol} should pass the factory's L{World} to the
        initializer of the protocol it creates.
        """
        world = object()
        factory = Gam3Factory(world)
        protocol = factory.buildProtocol(None)
        self.assertIdentical(protocol.world, world)


    def test_factory(self):
        """
        L{Gam3Factory} should be a Twisted Protocol Server Factory.
        """
        verifyObject(IProtocolFactory, Gam3Factory(None))
