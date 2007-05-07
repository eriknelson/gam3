# -*- test-case-name: game.test.test_controller -*-

"""
Input handling.
"""

from pygame import (K_LEFT as LEFT,
                    K_RIGHT as RIGHT,
                    K_UP as UP,
                    K_DOWN as DOWN)

from game.direction import WEST, EAST, NORTH, SOUTH


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
        direction = KEYS_TO_DIRECTIONS.get(key)
        if direction:
            direction = self.player.direction + KEYS_TO_DIRECTIONS[key]
            self.player.setDirection(direction)

    def keyUp(self, key):
        direction = KEYS_TO_DIRECTIONS.get(key)
        if direction:
            # XXX This should take into consideration the *current* direction.
            self.player.setDirection(None)
