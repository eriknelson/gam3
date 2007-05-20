"""
Tests for the networking functionality of Gam3.
"""

from zope.interface.verify import verifyObject

from twisted.trial.unittest import TestCase
from twisted.internet.interfaces import IProtocolFactory

from game.network import Introduce, SetDirectionOf, Direction, NewPlayer
from game.player import Player
from game.direction import WEST

from gam3.world import World
from gam3.network import Gam3Factory, Gam3Server



class FakeWorld(object):
    """
    Act like a L{gam3.world.World}.

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

    def addObserver(self, observer):
        """
        Do nothing.

        @param observer: A parameter.
        """



class NetworkTests(TestCase):
    """
    Tests for the client-facing AMP server protocol.

    @ivar calls: List of tuples of (AMP command class, dictionary of
        arguments).
    """

    def setUp(self):
        """
        Initialize C{self.calls}.
        """
        self.calls = []


    def callRemote(self, command, **kw):
        """
        Add a call to C{self.calls}.
        """
        self.calls.append((command, kw))


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


    def test_createMorePlayers(self):
        """
        When a player is created, all existing clients must be
        notified of it.
        """
        world = World()
        protocol = Gam3Server(world)
        protocol.callRemote = self.callRemote
        player = world.createPlayer()
        x, y = player.getPosition()
        self.assertEqual(
            self.calls,
            [(NewPlayer, {'identifier': protocol.identifierForPlayer(player),
                          'x': x, 'y': y, 'speed': player.speed})])


    def test_setDirection(self):
        """
        The server should respond to L{SetDirectionOf} commands and
        change direction of the specified L{Player} model object.
        """
        world = FakeWorld()
        player = world.createPlayer()

        protocol = Gam3Server(world)
        player_id = protocol.identifierForPlayer(player)
        responder = protocol.lookupFunction(SetDirectionOf.commandName)
        d = responder({"identifier": str(player_id),
                       "direction": Direction().toString(WEST)})

        def gotResult(box):
            self.assertEqual(player.direction, WEST)

        d.addCallback(gotResult)
        return d


    def test_identifierForPlayer(self):
        """
        L{Gam3Server} should provide an identifier producing function
        which produces identifiers that go up.
        """
        protocol = Gam3Server(FakeWorld())
        player1 = object()
        player2 = object()
        playerOneID = protocol.identifierForPlayer(player1)
        playerTwoID = protocol.identifierForPlayer(player2)
        self.assertEqual(protocol.identifierForPlayer(player1), playerOneID)
        self.assertEqual(protocol.identifierForPlayer(player2), playerTwoID)
        self.assertNotEqual(playerOneID, playerTwoID)


    def test_playerForIdentifier(self):
        """
        L{Gam3Server} should provide a function from L{Player}
        identifiers to L{Player}s.
        """
        protocol = Gam3Server(FakeWorld())
        player = object()
        playerID = protocol.identifierForPlayer(player)
        self.assertIdentical(protocol.playerForIdentifier(playerID), player)



class FactoryTests(TestCase):
    """
    Tests for L{Gam3Factory}.
    """
    def test_world(self):
        """
        L{Gam3Factory.buildProtocol} should pass the factory's L{World} to the
        initializer of the protocol it creates.
        """
        world = FakeWorld()
        factory = Gam3Factory(world)
        protocol = factory.buildProtocol(None)
        self.assertIdentical(protocol.world, world)


    def test_factory(self):
        """
        L{Gam3Factory} should be a Twisted Protocol Server Factory.
        """
        verifyObject(IProtocolFactory, Gam3Factory(None))
