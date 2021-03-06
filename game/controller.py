# -*- test-case-name: game.test.test_controller -*-

"""
Input handling.
"""

from pygame import (
    K_LEFT, K_RIGHT, K_UP, K_DOWN,
    K_w, K_a, K_s, K_d
)

from game.direction import (
    FORWARD, BACKWARD, LEFT, RIGHT,
    FORWARD_ZERO, SIDEWAYS_ZERO)


KEYS_TO_DIRECTIONS = {
    K_LEFT: LEFT,
    K_RIGHT: RIGHT,
    K_UP: FORWARD,
    K_DOWN: BACKWARD,
    K_w: FORWARD,
    K_a: LEFT,
    K_s: BACKWARD,
    K_d: RIGHT,
    }


class PlayerController(object):
    """
    Input handler for L{game.player.Player} objects.

    @ivar player: The player being controlled.
    @ivar downDirections: List of currently held arrow keys.

    @ivar mouseSensitivity: A multipler for how much rotation each unit of
        relative mouse movement should result in.
    """

    mouseSensitivity = 0.25

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
            try:
                self.downDirections.remove(key)
            except ValueError:
                pass
            else:
                self.player.setDirection(
                    self.calculateDirection(self.downDirections))


    def mouseMotion(self, position, (x, y), buttons):
        """
        Handle mouse motion to change the orientation of the player.
        """
        self.player.turn(
            y * self.mouseSensitivity, x * self.mouseSensitivity)


    def calculateDirection(self, pressedKeys):
        """
        Given a list of keys (sorted by their press-time), calculate
        the direction that the player should be moving in.
        """
        forwardDir = FORWARD_ZERO
        sidewaysDir = SIDEWAYS_ZERO

        if pressedKeys:
            for key in pressedKeys:
                direction = KEYS_TO_DIRECTIONS[key]
                if direction in (FORWARD, BACKWARD):
                    forwardDir = direction
                if direction in (LEFT, RIGHT):
                    sidewaysDir = direction
            return forwardDir + sidewaysDir
