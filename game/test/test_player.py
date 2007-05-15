from twisted.trial import unittest

from game.direction import NORTH, WEST, SOUTH, EAST
from game.player import Player
from game.test.util import PlayerCreationMixin


# XXX Test that the position is ints


class DirectionObserver(object):
    """
    Recorder implementation of the direction observer interface used to verify
    that direction observation works.

    @ivar changes: C{list} of three-tuples of player objects, positions, and
    directions.  One element per call to C{directionChanged}.
    """
    def __init__(self):
        self.changes = []


    def directionChanged(self, player):
        """
        Record a direction change event for the given player.

        @param player: The player which changed direction.
        """
        self.changes.append((
                player, player.getPosition(), player.direction))



class PlayerTests(unittest.TestCase, PlayerCreationMixin):
    """
    There should be an object which has a position and can be moved in
    eight directions.
    """
    def test_setPosition(self):
        """
        Players have a position which can be set with C{setPosition}.
        """
        player = self.makePlayer((1, 2))
        player.setPosition((-2, 1))
        self.assertEqual(player.getPosition(), (-2, 1))


    def test_setPositionAfterSomeMotion(self):
        """
        Players should be placed at the correct position if C{setPosition} is
        called after they have been moving around a little bit.
        """
        player = self.makePlayer((1, 2))
        player.setDirection(NORTH)
        self.advanceTime(1)
        player.setPosition((-2, 1))
        self.assertEqual(player.getPosition(), (-2, 1))


    def test_getPosition(self):
        """
        Players have a C{getPosition} method the initial return value of which
        is based on initializer parameters.
        """
        player = self.makePlayer((0, 0))
        self.assertEqual(player.getPosition(), (0, 0))


    def test_setDirection(self):
        """
        L{Player.setDirection} should accept a vector which sets the direction
        of the player's movement.
        """
        player = self.makePlayer((3, 2))
        player.setDirection(NORTH + EAST)
        self.assertEqual(player.direction, NORTH + EAST)
        player.setDirection(SOUTH)
        self.assertEqual(player.direction, SOUTH)


    def test_getPositionWithoutMovementAfterTimePasses(self):
        """
        Directionless L{Player}s should remain stationary.
        """
        position = (2, 3)
        player = self.makePlayer(position)
        self.advanceTime(10)
        self.assertEqual(player.getPosition(), position)


    def test_getPositionWithMovementAfterTimePasses(self):
        """
        Directed L{Player}s should change position.
        """
        x, y = 3, -2
        player = self.makePlayer((x, y))
        player.setDirection(WEST)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), (x - 1, y))


    def test_greaterVelocityResultsInGreaterDisplacement(self):
        """
        A L{Player} which is moving more quickly should travel further.
        """
        x, y = 2, 0
        velocity = 5
        player = self.makePlayer((x, y), movementVelocity=velocity)
        player.setDirection(EAST)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), (x + velocity, y))


    def test_getPositionWithMovementAfterTimePassesTwice(self):
        """
        Twice-directed players should have an accurate position after each
        change in direction after some time passes.
        """
        x, y = 3, -2
        player = self.makePlayer((x, y))
        player.setDirection(EAST)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), (x + 1, y))

        player.setDirection(NORTH)
        self.advanceTime(1)
        self.assertEquals(player.getPosition(), (x + 1, y + 1))


    def test_stop(self):
        """
        Setting the player's direction to C{None} should make the
        player cease moving.
        """
        x, y = 49, 27
        player = self.makePlayer((x, y))
        player.setDirection(None)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), (x, y))

        player.setDirection(EAST)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), (x + 1, y))

        player.setDirection(None)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), (x + 1, y))


    def test_observeDirection(self):
        """
        Setting the player's direction should notify any observers registered
        with that player of the new direction.
        """
        position = (6, 2)
        player = self.makePlayer(position)
        observer = DirectionObserver()
        player.addObserver(observer)
        player.setDirection(NORTH)
        self.assertEqual(observer.changes, [(player, position, NORTH)])


    def test_getPositionInsideObserver(self):
        """
        L{Player.getPosition} should return an accurate value when called
        within an observer's C{directionChanged} callback.
        """
        position = (1, 1)
        player = self.makePlayer(position)
        player.setDirection(EAST)
        self.advanceTime(1)
        observer = DirectionObserver()
        player.addObserver(observer)
        player.setDirection(None)
        self.assertEqual(observer.changes, [(player, (2, 1), None)])
