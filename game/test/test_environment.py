
"""
Tests for L{game.environment}.
"""

from twisted.trial.unittest import TestCase
from twisted.internet.task import Clock

from game.environment import Environment


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

