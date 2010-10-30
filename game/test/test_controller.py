
"""
Tests for L{game.controller}.
"""

from twisted.trial.unittest import TestCase

from game.controller import PlayerController, K_LEFT, K_RIGHT, K_UP, K_DOWN
from game.direction import FORWARD, BACKWARD, LEFT, RIGHT
from game.test.util import PlayerCreationMixin
from game.vec3 import vec3


class PlayerControllerTests(TestCase, PlayerCreationMixin):
    def setUp(self):
        """
        Set up a player and a controller.
        """
        self.player = self.makePlayer(vec3(2, 4, -6))
        self.controller = PlayerController(self.player)


    def test_ignore_unknown_keys(self):
        """
        The PlayerController should not flip out if it gets a key that
        it doesn't know about.
        """
        self.controller.keyDown(object())
        self.controller.keyUp(object())


    def _directionTest(self, keys, direction):
        """
        Test helper for intercardinal direction setting, e.g. forward and left,
        backwards and right, etc.

        @param keys: The keypresses to simulate.
        @param direction: The direction that should result.
        """
        for key in keys:
            self.controller.keyDown(key)
        self.assertEqual(self.player.direction, direction)
        for key in keys:
            self.controller.keyUp(key)
        self.assertEqual(self.player.direction, None)


    def test_moveLeft(self):
        """
        L{PlayerController.keyDown} should set the player's direction to LEFT if
        the input is K_LEFT.
        """
        self._directionTest([K_LEFT], LEFT)


    def test_moveRight(self):
        """
        Similar to L{test_moveLeft}, but for rightward movement.
        """
        return self._directionTest([K_RIGHT], RIGHT)


    def test_moveForward(self):
        """
        Similar to L{test_moveLeft}, but for forward movement.
        """
        return self._directionTest([K_UP], FORWARD)


    def test_moveBackward(self):
        """
        Similar to L{test_moveLeft}, but for backward movement.
        """
        return self._directionTest([K_DOWN], BACKWARD)


    def test_moveForwardAndRight(self):
        """
        Similar to L{test_moveLeft}, but for forward, rightward movement.
        """
        self._directionTest([K_UP, K_RIGHT], FORWARD + RIGHT)
        self._directionTest([K_RIGHT, K_UP], FORWARD + RIGHT)


    def test_moveForwardAndLeft(self):
        """
        Similar to L{test_moveLeft}, but for forward, leftward movement.
        """
        self._directionTest([K_UP, K_LEFT], FORWARD + LEFT)
        self._directionTest([K_LEFT, K_UP], FORWARD + LEFT)


    def test_moveBackwardAndLeft(self):
        """
        Similar to L{test_moveLeft}, but for backward, leftward movement.
        """
        self._directionTest([K_DOWN, K_LEFT], BACKWARD + LEFT)
        self._directionTest([K_LEFT, K_DOWN], BACKWARD + LEFT)


    def test_moveBackwardAndRight(self):
        """
        Similar to L{test_moveLeft}, but for backward, rightward movement.
        """
        self._directionTest([K_DOWN, K_RIGHT], BACKWARD + RIGHT)
        self._directionTest([K_RIGHT, K_DOWN], BACKWARD + RIGHT)


    def test_moveLeftThenRight(self):
        """
        Holding left and then holding right should make the player go right.
        """
        self.controller.keyDown(K_LEFT)
        self.controller.keyDown(K_RIGHT)
        self.assertEqual(self.player.direction, RIGHT)


    def test_moveLeftThenRightThenDropLeft(self):
        """
        Holding left, then holding right, then releasing left, should leave the
        player moving right.
        """
        self.controller.keyDown(K_LEFT)
        self.controller.keyDown(K_RIGHT)
        self.controller.keyUp(K_LEFT)
        self.assertEqual(self.player.direction, RIGHT)


    def test_moveLeftThenRightThenDropRight(self):
        """
        Holding left, then holding right, then releasing right, should leave the
        player moving left.
        """
        self.controller.keyDown(K_LEFT)
        self.controller.keyDown(K_RIGHT)
        self.controller.keyUp(K_RIGHT)
        self.assertEqual(self.player.direction, LEFT)


    def test_moveLeftThenRightThenForward(self):
        """
        Holding left, then holding right, then holding up should leave the
        player moving forward and rightward.

        NOTE: This will not actually work in many hardware configurations,
        probably because either keyboard hardware does not send enough
        simultaneous keydown events or the keyboard driver does not handle them.

        """
        self.controller.keyDown(K_LEFT)
        self.controller.keyDown(K_RIGHT)
        self.controller.keyDown(K_UP)
        self.assertEqual(self.player.direction, FORWARD + RIGHT)



class CalculateDirectionTest(TestCase, PlayerCreationMixin):
    """
    There should be a method for figuring out a direction based on
    currently-pressed keys (including the order they were pressed in).
    """

    def setUp(self):
        """
        Set up a player and a controller.
        """
        self.player = self.makePlayer(vec3(2, -8.5, 4))
        self.controller = PlayerController(self.player)


    def test_calculateNoDirection(self):
        """
        No inputs should equal no movement.
        """
        self.assertEqual(self.controller.calculateDirection([]), None)


    def test_calculateDirectionCardinal(self):
        """
        Any arrow key in isolation should return the appropriate
        cardinal direction.
        """
        self.assertEqual(self.controller.calculateDirection([K_RIGHT]), RIGHT)
        self.assertEqual(self.controller.calculateDirection([K_LEFT]), LEFT)
        self.assertEqual(self.controller.calculateDirection([K_UP]), FORWARD)
        self.assertEqual(self.controller.calculateDirection([K_DOWN]), BACKWARD)


    def test_calculateDirectionIntercardinal(self):
        """
        Any non-opposing arrow keys held simultaneously should produce the
        intercardinal direction between their associated directions.
        """
        directions = [((K_UP, K_RIGHT), FORWARD + RIGHT),
                      ((K_UP, K_LEFT), FORWARD + LEFT),
                      ((K_DOWN, K_LEFT), BACKWARD + LEFT),
                      ((K_DOWN, K_RIGHT), BACKWARD + RIGHT),
                      ]

        for arrows, answer in directions:
            self.assertEqual(self.controller.calculateDirection(arrows), answer)
            self.assertEqual(
                self.controller.calculateDirection(reversed(arrows)), answer)




    # XXX Test that PRESS-RIGHT, PRESS-DOWN, RELEASE-DOWN leaves the
    # player going RIGHT.



class MouseLookTests(TestCase, PlayerCreationMixin):
    """
    Tests for mouse motion events which control the direction the player is
    facing.
    """
    def setUp(self):
        """
        Set up a player and a controller.
        """
        self.player = self.makePlayer(vec3(2, 4, -6))
        self.controller = PlayerController(self.player)


    def test_lookLeft(self):
        """
        A mouse motion event with a negative relative X component rotates the
        player's perspective to the left.
        """
        self.controller.mouseMotion((100, 200), (-20, 20), None)
        self.assertEquals(self.player.orientation.y, -2)

