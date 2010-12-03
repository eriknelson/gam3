"""
Tests for the networking functionality of Gam3.
"""

from zope.interface.verify import verifyObject

from twisted.trial.unittest import TestCase
from twisted.internet.interfaces import IProtocolFactory
from twisted.internet.task import Clock
from twisted.test.proto_helpers import StringTransport

from game.vector import Vector
from game.network import (Introduce, SetMyDirection, SetDirectionOf,
                          Direction, NewPlayer, RemovePlayer, SetTerrain)
from game.player import Player
from game.direction import LEFT, RIGHT
from game.terrain import loadTerrainFromString

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
    x = 129.5
    y = -299999.5
    z = 3.5

    def __init__(self):
        self.players = []


    def createPlayer(self):
        """
        Create a L{Player}, recording it in C{self.players}.
        """
        self.players.append(
            Player(Vector(self.x, self.y, self.z), self.speed, lambda: 3))
        return self.players[-1]


    def addObserver(self, observer):
        """
        Do nothing.

        @param observer: A parameter.
        """


    def getPlayers(self):
        """
        Return the players.
        """
        return self.players



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


    def getCommands(self, commandClass):
        """
        Return a list of all of the commands of the given type which have been
        sent (and captured by the fake L{callRemote}).
        """
        return [
            (cmd, args) for (cmd, args) in self.calls if cmd is commandClass]


    def callRemote(self, command, **kw):
        """
        Add a call to C{self.calls}.
        """
        self.calls.append((command, kw))


    def test_defaultClock(self):
        """
        The L{Gam3Server}'s default clock should be
        L{twisted.internet.reactor}.
        """
        from twisted.internet import reactor
        protocol = Gam3Server(World())
        self.assertIdentical(protocol.clock, reactor)


    def test_introduction(self):
        """
        The server should respond to L{Introduce} commands with environment
        parameters and new player data.
        """
        world = FakeWorld()
        protocol = Gam3Server(world, clock=Clock())
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
                              'y': str(world.y),
                              'z': str(world.z)})

        d.addCallback(gotResult)
        return d


    def test_createMorePlayers(self):
        """
        When a player is created, all existing clients must be notified of it.
        """
        clock = Clock()
        world = World()
        protocol = Gam3Server(world, clock=clock)
        #Introduce the protocol to a client so that it starts watching
        #for new Players.
        protocol.callRemote = self.callRemote
        protocol.introduce()
        # advance because the observer doesn't start until later FIXME BUG XXX
        # see #2671
        clock.advance(0)
        player = world.createPlayer()
        v = player.getPosition()
        self.assertEqual(
            self.getCommands(NewPlayer),
            [(NewPlayer, {'identifier': protocol.identifierForPlayer(player),
                          'x': v.x, 'y': v.y, 'z': v.z,
                          'speed': player.speed})])


    def test_introductionDoesNotSendNewPlayer(self):
        """
        When introducing the first character, no L{NewPlayer} command should be
        sent.
        """
        world = World()
        protocol = Gam3Server(world)
        protocol.callRemote = self.callRemote
        protocol.introduce()
        self.assertEqual(self.calls, [])


    def test_noTerrain(self):
        """
        If the world is void and without form, no L{SetTerrain} command is sent
        after the introduction.
        """
        clock = Clock()
        world = World()

        protocol = Gam3Server(world, clock=clock)
        protocol.callRemote = self.callRemote

        protocol.introduce()

        # Advance because SetTerrain isn't sent until later FIXME BUG XXX see
        # #2671.
        clock.advance(0)

        self.assertEquals(self.getCommands(SetTerrain), [])


    def test_sendTerrain(self):
        """
        When a player connects and introduces himself, he should shortly
        thereafter get a L{SetTerrain} for the terrain surrounding his location.
        """
        clock = Clock()
        world = World()
        world.terrain = loadTerrainFromString("GGM\nMMD")

        protocol = Gam3Server(world, clock=clock)
        protocol.callRemote = self.callRemote

        protocol.introduce()

        # Advance because SetTerrain isn't sent until later FIXME BUG XXX see
        # #2671.
        clock.advance(0)

        self.assertEqual(
            self.getCommands(SetTerrain),
            # This comparison is allowed only because world.terrain is the same
            # object passed to SetTerrain.  Because they are identical, the
            # equality check is skipped.
            [(SetTerrain, {'x': 0, 'y': 0, 'z': 0, 'voxels': world.terrain})])


    def test_oldPlayerNewPlayer(self):
        """
        When a player connects and introduces himself, he should shortly
        thereafter get L{NewPlayer} commands for all already-connected players.
        """
        clock = Clock()
        world = World()

        player1 = world.createPlayer()

        protocol = Gam3Server(world, clock=clock)
        protocol.callRemote = self.callRemote

        # Try to create a player tricksily to invoke race conditions
        player2 = world.createPlayer()

        self.assertEqual(self.calls, [])

        protocol.introduce()

        # Try to create a player tricksily to invoke race conditions
        player3 = world.createPlayer()
        # advance because NewPlayers aren't sent until later FIXME BUG XXX
        # see #2671
        clock.advance(0)

        calls = self.getCommands(NewPlayer)
        self.assertEqual(len(calls), 3)

        for newPlayer in [(NewPlayer,
                           {"identifier": protocol.identifierForPlayer(player1),
                            "speed": player1.speed,
                            "x": player1.getPosition().x,
                            "y": player1.getPosition().y,
                            "z": player1.getPosition().z,
                            }),
                          (NewPlayer,
                           {"identifier": protocol.identifierForPlayer(player2),
                            "speed": player2.speed,
                            "x": player2.getPosition().x,
                            "y": player2.getPosition().y,
                            "z": player2.getPosition().z,
                            }),
                          (NewPlayer,
                           {"identifier": protocol.identifierForPlayer(player3),
                            "speed": player3.speed,
                            "x": player3.getPosition().x,
                            "y": player3.getPosition().y,
                            "z": player3.getPosition().z,
                            }),
                          ]:
            self.assertTrue(newPlayer in calls)


    def test_sendOtherPlayersDirection(self):
        """
        When other L{Player}s change direction, the client should be notified
        of the new direction and the position at the time of the change.
        """
        world = World()
        player = world.createPlayer()
        protocol = Gam3Server(world)
        protocol.callRemote = self.callRemote
        protocol.sendExistingPlayers()
        self.calls = []
        player.orientation.y = 1.5
        player.setDirection(LEFT)
        v = player.getPosition()
        self.assertEqual(self.calls,
                         [(SetDirectionOf,
                           {"identifier": protocol.identifierForPlayer(player),
                            "direction": LEFT,
                            "x": v.x,
                            "y": v.y,
                            "z": v.z,
                            "orientation": 1.5})])


    def test_sendOnlyOtherDirectionOfPlayers(self):
        """
        L{SetDirectionOf} commands should not be sent for the client's
        L{Player}.
        """
        clock = Clock()
        world = World()
        protocol = Gam3Server(world, clock=clock)
        protocol.callRemote = self.callRemote
        protocol.introduce()
        # advance because observers aren't registered until later FIXME BUG XXX
        # see #2671
        clock.advance(0)
        protocol.player.setDirection(LEFT)
        self.assertEqual(self.getCommands(SetDirectionOf), [])


    def test_sendDirectionOfNewPlayers(self):
        """
        L{Player}s who are added after a client has been introduced
        should have their directions and positions sent.
        """
        clock = Clock()
        world = World()
        protocol = Gam3Server(world, clock=clock)
        protocol.callRemote = self.callRemote
        protocol.introduce()
        # advance because observers aren't registered until later FIXME BUG XXX
        # see #2671
        clock.advance(0)
        player = world.createPlayer()
        self.calls = [] #ignore other calls
        player.orientation.y = -1.5
        player.setDirection(RIGHT)
        v = player.getPosition()
        self.assertEqual(self.calls,
                         [(SetDirectionOf,
                           {"identifier": protocol.identifierForPlayer(player),
                            "direction": RIGHT,
                            "x": v.x,
                            "y": v.y,
                            "z": v.z,
                            "orientation": -1.5})])


    def test_playerRemoved(self):
        """
        The L{Gam3Server} should respond to C{playerRemoved} events by sending a
        L{RemovePlayer} command and no longer tracking the removed L{Player}'s
        identifier.
        """
        world = World()
        protocol = Gam3Server(world)
        protocol.callRemote = self.callRemote
        player = world.createPlayer()
        protocol.sendExistingPlayers() # to start observing!
        del self.calls[0]
        identifier = protocol.identifierForPlayer(player)
        world.removePlayer(player)
        self.assertEqual(self.calls,
                         [(RemovePlayer, {'identifier': identifier})])
        self.assertRaises(KeyError, protocol.playerForIdentifier, identifier)


    def test_connectionLost(self):
        """
        The L{Gam3Server} should remove its L{Player} from the
        L{World} when its connection is lost.
        """
        world = World()
        protocol = Gam3Server(world)
        protocol.makeConnection(StringTransport())
        protocol.introduce()
        player = protocol.player
        protocol.connectionLost(None)
        self.assertFalse(player in world.players)


    def test_setMyDirection(self):
        """
        The server should respond to L{SetMyDirection} commands and
        change direction of the specified L{Player} model object.
        """
        world = FakeWorld()
        protocol = Gam3Server(world, clock=Clock())
        protocol.introduce()
        responder = protocol.lookupFunction(SetMyDirection.commandName)
        d = responder({"direction": Direction().toString(RIGHT),
                       'y': '1.5'})

        def gotResult(box):
            self.assertEquals(protocol.player.direction, RIGHT)
            self.assertEquals(protocol.player.orientation.y, 1.5)
            v = protocol.player.getPosition()
            self.assertEquals(box, {'x': str(v.x), 'y': str(v.y), 'z': str(v.z)})

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
