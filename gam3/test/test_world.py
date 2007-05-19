
"""
Tests for L{gam3.world}.
"""

from twisted.trial.unittest import TestCase

from epsilon.structlike import record

from gam3.world import World, point

from game.test.test_environment import SimulationTimeTestsMixin


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



class WorldTimeTests(SimulationTimeTestsMixin, TestCase):
    """
    Tests for the time-simulating aspecst of L{World}.
    """

    def get_simulation(self, granularity, scheduler):
        """
        Return a L{World}.
        """
        return World(granularity=granularity, scheduler=scheduler)

