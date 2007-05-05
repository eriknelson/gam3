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


    def test_movementObservation(self):
        """
        L{Player.move} should notify an observer that the movement occurred.
        """
        startPosition = (3, 2)
        player = Player(startPosition)

        class MovementObserver(object):
            def __init__(self):
                self.movements = []

            def moved(self, what, previousPosition):
                self.movements.append((what, previousPosition, what.position))
        observer = MovementObserver()

        # XXX Should this be addMovementObserver?
        player.addObserver(observer)
        player.move((-2, 1))
        self.assertEqual(observer.movements, [(player, startPosition, (1, 3))])
