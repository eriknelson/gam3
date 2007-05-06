
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


    # XXX: Uncomment second assertions (and make it pass by doing whatever else
    # you need to do as long as that assertion remains, you idioRt)
    def test_moveNortheast(self):
        """
        Similar to L{test_moveWest}, but for northeasterly movement.
        """
        self._directionTest([UP, RIGHT], NORTH + EAST)
#         self._directionTest([RIGHT, UP], NORTH + EAST)


    def test_moveNorthwest(self):
        """
        Similar to L{test_moveWest}, but for northwesterly movement.
        """
        self._directionTest([UP, LEFT], NORTH + WEST)
#         self._directionTest([LEFT, UP], NORTH + WEST)


    def test_moveSouthwest(self):
        """
        Similar to L{test_moveWest}, but for southwesterly movement.
        """
        self._directionTest([DOWN, LEFT], SOUTH + WEST)
#         self._directionTest([LEFT, DOWN], SOUTH + WEST)


    def test_moveSoutheast(self):
        """
        Similar to L{test_moveWest}, but for southeasterly movement.
        """
        self._directionTest([DOWN, RIGHT], SOUTH + EAST)
#         self._directionTest([RIGHT, DOWN], SOUTH + EAST)
