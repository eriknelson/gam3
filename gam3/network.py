# -*- test-case-name: gam3.test.test_network -*-

"""
Network functionality of Gam3.
"""

from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor
from twisted.protocols.amp import AMP

from game.network import Introduce, SetDirectionOf, NewPlayer, SetMyDirection


class Gam3Server(AMP):
    """
    Translate AMP requests from clients into model
    operations and vice versa

    @ivar world: The L{World}.
    @ivar players: A mapping from L{Player} identifiers to L{Player}s.
    @ivar clock: An L{IReactorTime} provider.
    @ivar player: The L{Player} of the client that this protocol
        instance is communicating to.
    """

    def __init__(self, world, clock=reactor):
        self.world = world
        self.clock = clock
        self.players = {}
        self.player = None


    def playerCreated(self, player):
        """
        Broadcast data about the new player to the client that this
        protocol is connected to with a L{NewPlayer} command.

        @param player: The L{Player} that was created.
        """
        self.notifyPlayerCreated(player)
        player.addObserver(self)


    def notifyPlayerCreated(self, player):
        """
        Notify the client that a new L{Player} has been created.
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
        identifier = self.identifierForPlayer(player)
        x, y = player.getPosition()
        # XXX FIXME BUG: Instead, we should do what twisted:#2671 wants.
        self.clock.callLater(0, self.sendExistingPlayers)
        self.player = player
        return {"granularity": self.world.granularity,
                "identifier": identifier,
                "speed": player.speed,
                "x": x,
                "y": y}
    Introduce.responder(introduce)


    def sendExistingPlayers(self):
        """
        Send L{NewCommand} commands to this client for each existing
        L{Player} in the L{World}.
        """
        for player in self.world.getPlayers():
            if player is not self.player:
                self.notifyPlayerCreated(player)
                player.addObserver(self)
        self.world.addObserver(self)


    # IPlayerObserver
    def directionChanged(self, player):
        """
        A L{Player}'s direction has changed: Send it to the client.
        """
        x, y = player.getPosition()
        self.callRemote(SetDirectionOf,
                        identifier=self.identifierForPlayer(player),
                        direction=player.direction,
                        x=x, y=y)

    # AMP responders
    def setMyDirection(self, direction):
        """
        Set the direction of the player of the client connected to this
        protocol.

        @param direction: A L{game.direction} direction.
        """
        self.player.setDirection(direction)
        x, y = self.player.getPosition()
        return {'x': x, 'y': y}
    SetMyDirection.responder(setMyDirection)


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
