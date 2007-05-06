# -*- test-case-name: game.test.test_controller -*-

"""
Input handling.
"""

from game.direction import WEST, EAST, NORTH, SOUTH


LEFT = 'left'
RIGHT = 'right'
UP = 'up'
DOWN = 'down'

KEYS_TO_DIRECTIONS = {
    LEFT: WEST,
    RIGHT: EAST,
    UP: NORTH,
    DOWN: SOUTH,
    }


class PlayerController(object):
    """
    Input handler for L{game.player.Player} objects.

    @ivar player: The player being controlled.
    """

    def __init__(self, player):
        self.player = player


    def keyDown(self, key):
        """
        Set C{self.player} into motion in response to arrow keys being pressed.
        """
        direction = self.player.direction + KEYS_TO_DIRECTIONS[key]
        self.player.setDirection(direction)
