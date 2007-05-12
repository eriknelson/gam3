"""
Tests for L{game.network} (Network support for Game).
"""

from twisted.trial.unittest import TestCase

from game.test.util import PlayerCreationMixin
from game.network import NetworkPlayerController, SetPosition, SetDirection, Direction
from game.direction import NORTH, SOUTH, EAST, WEST


class ControllerTests(TestCase, PlayerCreationMixin):
    """
    Tests for the bit that takes network input and controls the Player model,
    which is L{NetworkPlayerController}.
    """

    def test_setPosition(self):
        """
        When L{SetPosition} is issued the L{Player}'s position should be set.
        """
        player = self.makePlayer((1, 2))
        controller = NetworkPlayerController(player)

        responder = controller.lookupFunction(SetPosition.commandName)
        d = responder({'x': '23', 'y': '32'})

        def gotPositionSetting(ign):
            self.assertEqual(player.getPosition(), (23, 32))
        d.addCallback(gotPositionSetting)
        return d


    def test_setDirection(self):
        """
        When L{SetDirection} is issued, the L{Player}'s direction should be set.
        """
        player = self.makePlayer((1, 2))
        controller = NetworkPlayerController(player)

        responder = controller.lookupFunction(SetDirection.commandName)
        d = responder({'direction': Direction().toString(NORTH)})

        def gotDirectionSetting(ign):
            self.assertEqual(player.direction, NORTH)
        d.addCallback(gotDirectionSetting)
        return d



class DirectionArgumentTests(TestCase):
    """
    Tests for L{Direction}.
    """
    def test_cardinalConversion(self):
        """
        The cardinal directions should round trip through the L{Complex}
        argument.
        """
        argument = Direction()
        for direction in (NORTH, SOUTH, EAST, WEST):
            netrepr = argument.toString(direction)
            self.assertIdentical(type(netrepr), str)
            self.assertEqual(argument.fromString(netrepr), direction)


    def test_intercardinalConversion(self):
        """
        The intercardinal directions should round trip through the L{Complex}
        argument.
        """
        argument = Direction()
        for latitudinalSign in (NORTH, SOUTH):
            for longitudinalSign in (EAST, WEST):
                direction = latitudinalSign + longitudinalSign
                netrepr = argument.toString(direction)
                self.assertIdentical(type(netrepr), str)
                self.assertEqual(argument.fromString(netrepr), direction)
