
"""
Tests for L{game.controller}.
"""

from twisted.trial.unittest import TestCase

from game.controller import PlayerController, LEFT, RIGHT, UP, DOWN
from game.player import Player
from game.direction import NORTH, WEST, EAST, SOUTH
from game.test.util import PlayerCreationMixin


class PlayerControllerTests(TestCase, PlayerCreationMixin):
    def setUp(self):
        """
        Set up a player and a controller.
        """
        self.player = self.makePlayer((2, 4))
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
        Test helper for intercardinal direction setting, e.g. northeast,
        southwest, etc.

        @param keys: The keypresses to simulate.
        @param direction: The direction that should result.
        """
        for key in keys:
            self.controller.keyDown(key)
        self.assertEqual(self.player.direction, direction)
        for key in keys:
            self.controller.keyUp(key)
        self.assertEqual(self.player.direction, None)


    def test_moveWest(self):
        """
        L{PlayerController.keyDown} should set the player's direction to WEST
        if the input is LEFT.
        """
        self._directionTest([LEFT], WEST)


    def test_moveEast(self):
        """
        Similar to L{test_moveWest}, but for eastearn movement.
        """
        return self._directionTest([RIGHT], EAST)


    def test_moveNorth(self):
        """
        Similar to L{test_moveWest}, but for northern movement.
        """
        return self._directionTest([UP], NORTH)


    def test_moveSouth(self):
        """
        Similar to L{test_moveWest}, but for southern movement.
        """
        return self._directionTest([DOWN], SOUTH)


    def test_moveNortheast(self):
        """
        Similar to L{test_moveWest}, but for northeasterly movement.
        """
        self._directionTest([UP, RIGHT], NORTH + EAST)
        self._directionTest([RIGHT, UP], NORTH + EAST)


    def test_moveNorthwest(self):
        """
        Similar to L{test_moveWest}, but for northwesterly movement.
        """
        self._directionTest([UP, LEFT], NORTH + WEST)
        self._directionTest([LEFT, UP], NORTH + WEST)


    def test_moveSouthwest(self):
        """
        Similar to L{test_moveWest}, but for southwesterly movement.
        """
        self._directionTest([DOWN, LEFT], SOUTH + WEST)
        self._directionTest([LEFT, DOWN], SOUTH + WEST)


    def test_moveSoutheast(self):
        """
        Similar to L{test_moveWest}, but for southeasterly movement.
        """
        self._directionTest([DOWN, RIGHT], SOUTH + EAST)
        self._directionTest([RIGHT, DOWN], SOUTH + EAST)


    def test_moveEastThenWest(self):
        """
        Holding left and then holding right should make the player go east.
        """
        self.controller.keyDown(LEFT)
        self.controller.keyDown(RIGHT)
        self.assertEqual(self.player.direction, EAST)


    def test_moveEastThenWestThenDropEast(self):
        """
        Holding left, then holding right, then releasing left, should
        leave the player moving EAST.
        """
        self.controller.keyDown(LEFT)
        self.controller.keyDown(RIGHT)
        self.controller.keyUp(LEFT)
        self.assertEqual(self.player.direction, EAST)


    def test_moveWestThenEastThenDropEast(self):
        """
        Holding left, then holding right, then releasing right, should
        leave the player moving WEST.
        """
        self.controller.keyDown(LEFT)
        self.controller.keyDown(RIGHT)
        self.controller.keyUp(RIGHT)
        self.assertEqual(self.player.direction, WEST)


    def test_moveWestThenEastThenNorth(self):
        """
        Holding left, then holding right, then holding up should leave
        the player moving NORTH + EAST.

        NOTE: This will not actually work in many hardware
        configurations, probably because either keyboard hardware does
        not send enough simultaneous keydown events or the keyboard
        driver does not handle them.

        """
        self.controller.keyDown(LEFT)
        self.controller.keyDown(RIGHT)
        self.controller.keyDown(UP)
        self.assertEqual(self.player.direction, NORTH + EAST)



class CalculateDirectionTest(TestCase, PlayerCreationMixin):
    """
    There should be a method for figuring out a direction based on
    currently-pressed keys (including the order they were pressed in).
    """

    def setUp(self):
        """
        Set up a player and a controller.
        """
        self.player = self.makePlayer((2, 4))
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
        self.assertEqual(self.controller.calculateDirection([RIGHT]), EAST)
        self.assertEqual(self.controller.calculateDirection([LEFT]), WEST)
        self.assertEqual(self.controller.calculateDirection([UP]), NORTH)
        self.assertEqual(self.controller.calculateDirection([DOWN]), SOUTH)


    def test_calculateDirectionIntercardinal(self):
        """
        Any non-opposing arrow keys held simultaneously should produce
        the intercardinal direction between their associated
        directions.
        """
        directions = [((UP, RIGHT), NORTH + EAST),
                      ((UP, LEFT), NORTH + WEST),
                      ((DOWN, LEFT), SOUTH + WEST),
                      ((DOWN, RIGHT), SOUTH + EAST),
                      ]

        for arrows, answer in directions:
            self.assertEqual(self.controller.calculateDirection(arrows), answer)
            self.assertEqual(
                self.controller.calculateDirection(reversed(arrows)), answer)




    # XXX Test that PRESS-RIGHT, PRESS-DOWN, RELEASE-DOWN leaves the
    # player going EAST.
