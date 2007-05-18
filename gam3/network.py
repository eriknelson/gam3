# -*- test-case-name: gam3.test.test_network -*-

"""
Network functionality of Gam3.
"""

from twisted.protocols.amp import AMP

from game.network import Introduce


class Gam3Server(AMP):
    """
    Translate AMP requests from clients into model
    operations and vice versa

    @ivar world: The L{World}.
    """

    def __init__(self, world):
        self.world = world


    def introduce(self):
        """
        Return L{game.environment.Environment} and new
        L{game.player.Player} data.
        """
        player = self.world.createPlayer()
        identifier = self.identifierForPlayer(player)
        x, y = player.getPosition()
        return {"granularity": self.world.granularity,
                "identifier": identifier,
                "speed": player.speed,
                "x": x,
                "y": y}
    Introduce.responder(introduce)


    def identifierForPlayer(self, player):
        """
        Return an identifier for the given L{Player}. If the given
        L{Player} has not been given before, invent a new identifier.
        """
        return id(player)
