
"""
Tests for L{game.environment}.
"""

from twisted.trial.unittest import TestCase
from twisted.internet.task import Clock

from game.environment import Environment, SimulationTime
from game.test.util import PlayerCreationObserver


class SimulationTimeTestsMixin(object):
    """
    A mixin for tests which use L{SimulationTime}.
    """

    def setUp(self):
        """
        Set up a SimulationTime.
        """
        self.clock = Clock()
        self.simulation = self.getSimulationTime(1, self.clock)
        self.simulation.start()


    def test_initialTime(self):
        """
        The simulation's clock should start at zero.
        """
        self.assertEqual(self.simulation.seconds(), 0)


    def test_advance(self):
        """
        It should be possible to move the simulation's clock forward by a
        specified amount of time.
        """
        self.simulation.advance(3)
        self.assertEqual(self.simulation.seconds(), 3)
        self.simulation.advance(2)
        self.assertEqual(self.simulation.seconds(), 5)


    def test_updates(self):
        """
        The L{SimulationTime} should advance itself using the scheduler provided
        to its initializer.
        """
        for i in range(3):
            self.assertEqual(self.simulation.seconds(), i)
            self.clock.advance(1)
        self.assertEqual(self.simulation.seconds(), 3)

    def test_granularity(self):
        """
        The C{granularity} parameter to L{SimulationTime} should specify
        the number of times to update the model per second, based on
        the scheduler.
        """
        self.clock.advance(0.5)
        self.assertEqual(self.simulation.seconds(), 0)
        self.clock.advance(0.5)
        self.assertEqual(self.simulation.seconds(), 1)


    def test_subsecond_granularity(self):
        """
        Same as L{test_granularity}, but with subsecond granularity.
        """
        simulation = self.getSimulationTime(2, self.clock)
        simulation.start()
        self.clock.advance(0.5)
        self.assertEqual(simulation.seconds(), 0.5)
        self.clock.advance(0.5)
        self.assertEqual(simulation.seconds(), 1)


    def test_start(self):
        """
        There should be a way to start the simulation separately from
        instantiating it.
        """
        simulation = self.getSimulationTime(2, self.clock)
        self.clock.advance(10)
        self.assertEqual(simulation.seconds(), 0)


    def test_stop(self):
        """
        There should be a way to stop the simulation thus cancelling
        all scheduled calls.
        """
        self.assertEqual(len(self.clock.calls), 1)
        self.simulation.stop()
        self.assertEqual(self.clock.calls, [])



class SimulationTimeTests(SimulationTimeTestsMixin, TestCase):
    """
    Tests for L{SimulationTime}.
    """
    def getSimulationTime(self, granularity, clock):
        """
        Return a L{SimulationTime}.
        """
        return SimulationTime(granularity, clock)



class EnvironmentTimeTests(SimulationTimeTestsMixin, TestCase):
    """
    Tests for the L{SimulationTime} aspects of L{Environment}.
    """

    def getSimulationTime(self, granularity, scheduler):
        """
        Return a L{SimulationTime}.
        """
        return Environment(granularity, scheduler)



class EnvironmentTests(TestCase):
    """
    Tests for L{game.environment.Environment}.
    """

    def setUp(self):
        """
        Create an L{Environment} attached to a L{Clock} so that its behavior is
        deterministic.
        """
        self.clock = Clock()
        self.environment = Environment(1, self.clock)
        self.environment.start()


    def test_createPlayer(self):
        """
        L{Environment.createPlayer} should instantiate a L{Player} and
        broadcast it to all registered observers.
        """
        position = (1, 2)
        speed = 20
        observer = PlayerCreationObserver()
        self.environment.addObserver(observer)
        player = self.environment.createPlayer(position, speed)
        self.assertEqual(observer.createdPlayers, [player])
        self.assertEqual(player.getPosition(), position)
        self.assertEqual(player.speed, speed)
        self.assertEqual(player.seconds, self.environment.seconds)


    def test_setInitialPlayer(self):
        """
        L{Environment.setInitialPlayer} should change the environment's
        C{initialPlayer} attribute from C{None} to its argument.
        """
        self.assertIdentical(self.environment.initialPlayer, None)
        player = object()
        self.environment.setInitialPlayer(player)
        self.assertIdentical(self.environment.initialPlayer, player)
