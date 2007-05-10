# -*- test-case-name: game.test.test_controller -*-

"""
Input handling.
"""

from pygame import (K_LEFT as LEFT,
                    K_RIGHT as RIGHT,
                    K_UP as UP,
                    K_DOWN as DOWN)

from game.direction import (WEST, EAST, NORTH, SOUTH,
                            NORTH_SOUTH_ZERO, EAST_WEST_ZERO)


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
    @ivar downDirections: List of currently held arrow keys.
    """

    def __init__(self, player):
        self.player = player
        self.downDirections = []


    def keyDown(self, key):
        """
        Set C{self.player} into motion in response to arrow keys being pressed.

        @type key: L{game} key identifier.
        @param key: The key which is being pressed.
        """
        if key in KEYS_TO_DIRECTIONS:
            self.downDirections.append(key)
            self.player.setDirection(
                self.calculateDirection(self.downDirections))

    def keyUp(self, key):
        """
        Set C{self.player} into motion (or lack of it) in response to
        arrow keys being released.

        @type key: L{game} key identifier.
        @param key: The key which is being released.
        """
        if key in KEYS_TO_DIRECTIONS:
            self.downDirections.remove(key)
            self.player.setDirection(
                self.calculateDirection(self.downDirections))


    def calculateDirection(self, pressedKeys):
        """
        Given a list of keys (sorted by their press-time), calculate
        the direction that the player should be moving in.
        """
        northSouthDir = NORTH_SOUTH_ZERO
        eastWestDir = EAST_WEST_ZERO

        if pressedKeys:
            for key in pressedKeys:
                direction = KEYS_TO_DIRECTIONS[key]
                if direction in (NORTH, SOUTH):
                    northSouthDir = direction
                if direction in (WEST, EAST):
                    eastWestDir = direction
            return northSouthDir + eastWestDir
