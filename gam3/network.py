# -*- test-case-name: gam3.test.test_network -*-

"""
Network functionality of Gam3.
"""

from twisted.internet.protocol import ServerFactory
from twisted.protocols.amp import AMP

from game.network import Introduce, SetDirectionOf, NewPlayer


class Gam3Server(AMP):
    """
    Translate AMP requests from clients into model
    operations and vice versa

    @ivar world: The L{World}.
    @ivar players: A mapping from L{Player} identifiers to L{Player}s.
    """

    def __init__(self, world):
        self.world = world
        self.players = {}


    def playerCreated(self, player):
        """
        Broadcast data about the new player to the client that this
        protocol is connected to with a L{NewPlayer} command.

        @param player: The L{Player} that was created.
        """
        x, y = player.getPosition()
        self.callRemote(NewPlayer,
                        identifier=self.identifierForPlayer(player),
                        x=x, y=y, speed=player.speed)


    def introduce(self):
        """
        Return L{game.environment.Environment} and new
        L{game.player.Player} data, and start watching for new player
        creation.
        """
        player = self.world.createPlayer()
        self.world.addObserver(self)
        identifier = self.identifierForPlayer(player)
        x, y = player.getPosition()
        return {"granularity": self.world.granularity,
                "identifier": identifier,
                "speed": player.speed,
                "x": x,
                "y": y}
    Introduce.responder(introduce)


    def setDirectionOf(self, identifier, direction):
        """
        Set the direction of the player specified by the given identifier.

        @param identifier: A number specifying the L{Player} whose
            direction to change.
        @param direction: A L{game.direction} direction.
        """
        self.playerForIdentifier(identifier).setDirection(direction)
        return {}
    SetDirectionOf.responder(setDirectionOf)


    def identifierForPlayer(self, player):
        """
        Return an identifier for the given L{Player}. If the given
        L{Player} has not been given before, invent a new identifier.
        """
        self.players[id(player)] = player
        return id(player)


    def playerForIdentifier(self, identifier):
        """
        Return a L{Player} object for the given C{identifier}. The
        C{identifier} must be one of the identifiers returned from
        L{identifierForPlayer}.
        """
        return self.players[identifier]



class Gam3Factory(ServerFactory):
    """
    Server factory for Gam3.

    @ivar world: The L{World} which will be served by protocols created by this
    factory.
    """
    def __init__(self, world):
        self.world = world


    def buildProtocol(self, ignored):
        """
        Instantiate a L{Gam3Server} with a L{World}.
        """
        return Gam3Server(self.world)
