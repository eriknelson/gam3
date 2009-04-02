
"""
Tests for L{gam3.world}.
"""

from zope.interface.verify import verifyObject

from twisted.trial.unittest import TestCase
from twisted.internet.task import Clock
from twisted.application.service import IService

from epsilon.structlike import record

from gam3.world import Gam3Service, World, point

from game.test.test_environment import SimulationTimeTestsMixin
from game.test.util import PlayerVisibilityObserver


class StubRandom(record('rangeResults')):
    """
    Pretend to be a L{random.Random} object, but behave deterministically.

    @ivar rangeResults: A dict mapping L{randrange} argument tuples to the
    result which will be returned.
    """
    def randrange(self, start, stop):
        """
        Return the precomputed random result for the given range.
        """
        return self.rangeResults.pop((start, stop))



class WorldTests(TestCase):
    """
    Tests for L{World}.
    """

    def test_createPlayer(self):
        """
        L{World.createPlayer} should return a L{Player} at a random location
        within a specified rectangle.
        """
        bottomLeft = point(3, 7)
        topRight = point(21, 19)
        x, y = 7, 15

        random = StubRandom({(bottomLeft.x, topRight.x): x,
                             (bottomLeft.y, topRight.y): y})

        world = World(random, (bottomLeft, topRight))
        player = world.createPlayer()

        self.assertEqual(player.getPosition(), (x, y))


    def test_removePlayer(self):
        """
        L{World.removePlayer} should remove the given player from the
        world and broadcast an event about its removal.
        """
        world = World()
        player = world.createPlayer()
        observer = PlayerVisibilityObserver()
        world.addObserver(observer)
        world.removePlayer(player)
        self.assertFalse(player in world.players)
        self.assertEqual(observer.removedPlayers, [player])


    def test_removePlayerCallsObserversAfterRemovingPlayer(self):
        """
        In a C{playerRemoved} observer, the L{Player} who is being
        removed should not presently be a part of the L{World}.
        """
        world = World()
        player = world.createPlayer()
        existentPlayers = []

        class Observer(object):
            def playerRemoved(self, player):
                """
                An observer which records whether players are in the
                world.
                """
                existentPlayers.append(player in world.players)

        world.addObserver(Observer())
        world.removePlayer(player)
        self.assertEqual(existentPlayers, [False])


    def test_createdPlayerIsTemporallyAligned(self):
        """
        L{World.createPlayer} should create a player in the same time continuum
        as the L{World} it is called on.
        """
        world = World()
        player = world.createPlayer()
        self.assertEqual(player.seconds, world.seconds)


    def test_createPlayerWithDefaultWorld(self):
        """
        A L{World} instantiated with no arguments to C{__init__} should still
        be able to create a L{Player}.
        """
        world = World()
        player = world.createPlayer()
        x, y = player.getPosition()
        self.assertTrue(isinstance(x, int))
        self.assertTrue(isinstance(y, int))


    def test_createPlayerEmitsEvent(self):
        """
        When L{World.createPlayer} is called, observers should be
        notified.
        """
        world = World()
        observer = PlayerVisibilityObserver()
        world.addObserver(observer)
        player = world.createPlayer()
        self.assertEqual(observer.createdPlayers, [player])


    def test_getPlayers(self):
        """
        There should be a method for getting the L{Player}s from a
        L{World}.
        """
        world = World()
        player1 = world.createPlayer()
        player2 = world.createPlayer()
        self.assertEqual(list(world.getPlayers()), [player1, player2])


class WorldTimeTests(SimulationTimeTestsMixin, TestCase):
    """
    Tests for the time-simulating aspecst of L{World}.
    """

    def getSimulationTime(self, granularity, clock):
        """
        Return a L{World}.
        """
        return World(granularity=granularity, platformClock=clock)



class ServiceTests(TestCase):
    """
    Tests for L{Gam3Service}.
    """
    def test_serviceness(self):
        """
        L{Gam3Service} should provide L{IService}.
        """
        verifyObject(IService, Gam3Service(None))


    def test_startServiceStartsWorld(self):
        """
        L{Gam3Service.startService} should start simulation time.
        """
        clock = Clock()
        world = World(platformClock=clock)
        service = Gam3Service(world)
        self.assertFalse(clock.calls)
        service.startService()
        self.assertTrue(clock.calls)


    def test_stopServiceStopsWorld(self):
        """
        L{Gam3Service.stopService} should stop simulation time.
        """
        clock = Clock()
        world = World(platformClock=clock)
        service = Gam3Service(world)
        world.start()
        self.assertTrue(clock.calls)
        service.stopService()
        self.assertFalse(clock.calls)
