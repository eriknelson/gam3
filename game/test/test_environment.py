
"""
Tests for L{game.environment}.
"""

from twisted.trial.unittest import TestCase
from twisted.internet.task import Clock

from game.environment import Environment
from game.test.util import PlayerCreationObserver


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
        self.environment = Environment(1, self.clock.callLater)
        self.environment.start()


    def test_initialTime(self):
        """
        The environment's clock should start at zero.
        """
        self.assertEqual(self.environment.seconds(), 0)


    def test_advance(self):
        """
        It should be possible to move the environment's clock forward by a
        specified amount of time.
        """
        self.environment.advance(3)
        self.assertEqual(self.environment.seconds(), 3)
        self.environment.advance(2)
        self.assertEqual(self.environment.seconds(), 5)


    def test_updates(self):
        """
        The L{Environment} should advance itself using the scheduler provided
        to its initializer.
        """
        for i in range(3):
            self.assertEqual(self.environment.seconds(), i)
            self.clock.advance(1)
        self.assertEqual(self.environment.seconds(), 3)

    def test_granularity(self):
        """
        The C{granularity} parameter to L{Environment} should specify
        the number of times to update the model per second, based on
        the scheduler.
        """
        self.clock.advance(0.5)
        self.assertEqual(self.environment.seconds(), 0)
        self.clock.advance(0.5)
        self.assertEqual(self.environment.seconds(), 1)


    def test_subsecond_granularity(self):
        """
        Same as L{test_granularity}, but with subsecond granularity.
        """
        environment = Environment(2, self.clock.callLater)
        environment.start()
        self.clock.advance(0.5)
        self.assertEqual(environment.seconds(), 0.5)
        self.clock.advance(0.5)
        self.assertEqual(environment.seconds(), 1)


    def test_start(self):
        """
        There should be a way to start the environment separately from
        instantiating it.
        """
        environment = Environment(2, self.clock.callLater)
        self.clock.advance(10)
        self.assertEqual(environment.seconds(), 0)


    def test_stop(self):
        """
        There should be a way to stop the environment thus cancelling
        all scheduled calls.
        """
        self.assertEqual(len(self.clock.calls), 1)
        self.environment.stop()
        self.assertEqual(self.clock.calls, [])


    def _playerCreationTest(self, voluble):
        position = (1, 2)
        movementVelocity = 20
        observer = PlayerCreationObserver()
        self.environment.addObserver(observer)
        player = self.environment.createPlayer(position, movementVelocity, voluble)
        self.assertEqual(observer.createdPlayers, [(player, voluble)])
        self.assertEqual(player.getPosition(), position)
        self.assertEqual(player.movementVelocity, movementVelocity)
        self.assertEqual(player.seconds, self.environment.seconds)


    def test_createPlayer(self):
        """
        L{Environment.createPlayer} should instantiate a L{Player} and
        broadcast it to all registered observers.
        """
        return self._playerCreationTest(False)


    def test_createVolublePlayer(self):
        """
        As demonstrated by L{test_createPlayer}, save for the specification of
        a voluble player, which information should be propagated to observers.
        """
        return self._playerCreationTest(True)
