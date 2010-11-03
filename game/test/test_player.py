from twisted.trial import unittest

from game.direction import FORWARD, BACKWARD, LEFT, RIGHT
from game.test.util import PlayerCreationMixin
from game.player import Vertex


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
        player = self.makePlayer(Vertex(1, 0, 2))
        player.setPosition(Vertex(-2, 0, 1))
        self.assertEqual(player.getPosition(), Vertex(-2, 0, 1))


    def test_setPositionAfterSomeMotion(self):
        """
        Players should be placed at the correct position if C{setPosition} is
        called after they have been moving around a little bit.
        """
        player = self.makePlayer(Vertex(1, 0, 2))
        player.setDirection(FORWARD)
        self.advanceTime(1)
        player.setPosition(Vertex(-2, 0, 1))
        self.assertEqual(player.getPosition(), Vertex(-2, 0, 1))


    def test_getPosition(self):
        """
        Players have a C{getPosition} method the initial return value of which
        is based on initializer parameters.
        """
        player = self.makePlayer(Vertex(0, 0, 0))
        v = player.getPosition()
        self.assertEqual(v, Vertex(0, 0, 0))


    def test_setDirection(self):
        """
        L{Player.setDirection} should accept a vector which sets the direction
        of the player's movement.
        """
        player = self.makePlayer(Vertex(3, 0, 2))
        player.setDirection(FORWARD + LEFT)
        self.assertEqual(player.direction, FORWARD + LEFT)
        player.setDirection(BACKWARD)
        self.assertEqual(player.direction, BACKWARD)


    def test_getPositionWithoutMovementAfterTimePasses(self):
        """
        Directionless L{Player}s should remain stationary.
        """
        position = Vertex(2, 5, 3)
        player = self.makePlayer(position)
        self.advanceTime(10)
        self.assertEqual(player.getPosition(), position)


    def test_getPositionWithMovementAfterTimePasses(self):
        """
        Directed L{Player}s should change position.
        """
        v = Vertex(3, 0, -2)
        player = self.makePlayer(v)
        player.setDirection(LEFT)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), Vertex(v.x - 1, v.y, v.z))


    def test_greaterSpeedResultsInGreaterDisplacement(self):
        """
        A L{Player} which is moving more quickly should travel further.
        """
        v = Vertex(2, 3, 0)
        speed = 5
        player = self.makePlayer(v, speed=speed)
        player.setDirection(RIGHT)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), Vertex(v.x + speed, v.y, v.z))


    def test_getPositionWithMovementAfterTimePassesTwice(self):
        """
        Twice-directed players should have an accurate position after each
        change in direction after some time passes.
        """
        v = Vertex(3, 0, -2)
        player = self.makePlayer(v)
        player.setDirection(RIGHT)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), Vertex(v.x + 1, v.y, v.z))

        player.setDirection(FORWARD)
        self.advanceTime(1)
        self.assertEquals(player.getPosition(), Vertex(v.x + 1, v.y, v.z - 1))


    def test_getPositionFloats(self):
        """
        L{Player.getPosition} will returns C{float} values if the player's
        coordinates don't fall exactly onto integer values.
        """
        player = self.makePlayer(Vertex(0, 0, 0))
        player.setDirection(FORWARD)
        self.advanceTime(0.5)
        self.assertEquals(player.getPosition(), Vertex(0, 0, -0.5))


    def test_stop(self):
        """
        Setting the player's direction to C{None} makes the player cease moving.
        """
        x, y = 49, 27
        player = self.makePlayer(Vertex(x, 0, y))
        player.setDirection(None)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), Vertex(x, 0, y))

        player.setDirection(RIGHT)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), Vertex(x + 1, 0, y))

        player.setDirection(None)
        self.advanceTime(1)
        self.assertEqual(player.getPosition(), Vertex(x + 1, 0, y))


    def test_observeDirection(self):
        """
        Setting the player's direction should notify any observers registered
        with that player of the new direction.
        """
        position = Vertex(6, 3, 2)
        player = self.makePlayer(position)
        observer = DirectionObserver()
        player.addObserver(observer)
        player.setDirection(FORWARD)
        self.assertEqual(observer.changes, [(player, position, FORWARD)])


    def test_getPositionInsideObserver(self):
        """
        L{Player.getPosition} should return an accurate value when called
        within an observer's C{directionChanged} callback.
        """
        position = Vertex(1, 0, 1)
        player = self.makePlayer(position)
        player.setDirection(RIGHT)
        self.advanceTime(1)
        observer = DirectionObserver()
        player.addObserver(observer)
        player.setDirection(None)
        self.assertEqual(observer.changes, [(player, Vertex(2, 0, 1), None)])
