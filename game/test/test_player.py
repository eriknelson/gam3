from twisted.trial import unittest

from game.player import Player


class PlayerTests(unittest.TestCase):
    """
    There should be an object which has a position and can be moved in
    eight directions.
    """

    def test_position(self):
        """
        Players have a position attribute which is initialized based on
        initializer parameters.
        """
        player = Player((0, 0))
        self.assertEqual(player.position, (0, 0))

    
    def test_move(self):
        """
        L{Player.move} should accept an vector which will be applied
        to the player's position.
        """
        player = Player((2, 3))
        player.move((1, -2))
        self.assertEqual(player.position, (3, 1))
