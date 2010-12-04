# -*- test-case-name: gam3.test.test_network -*-

"""
Network functionality of Gam3.
"""

from twisted.internet.protocol import ServerFactory
from twisted.internet import reactor
from twisted.protocols.amp import AMP

from game.network import (
    Introduce, SetDirectionOf, NewPlayer, SetMyDirection, RemovePlayer,
    GetTerrain, SetTerrain)


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
        Send data about the new player to the client that this
        protocol is connected to with a L{NewPlayer} command.

        @param player: The L{Player} that was created.
        """
        self.notifyPlayerCreated(player)
        player.addObserver(self)


    def playerRemoved(self, player):
        """
        Send data about the removed player to the client that this
        protocol is connected to with a L{RemovePlayer} command.

        @param player: The L{Player} that was removed.
        """
        identifier = self.identifierForPlayer(player)
        self.callRemote(RemovePlayer, identifier=identifier)
        del self.players[identifier]


    def notifyPlayerCreated(self, player):
        """
        Notify the client that a new L{Player} has been created.
        """
        v = player.getPosition()
        self.callRemote(NewPlayer,
                        identifier=self.identifierForPlayer(player),
                        x=v.x, y=v.y, z=v.z, speed=player.speed)


    def introduce(self):
        """
        Return L{game.environment.Environment} and new
        L{game.player.Player} data, and start watching for new player
        creation.
        """
        player = self.world.createPlayer()
        identifier = self.identifierForPlayer(player)
        v = player.getPosition()
        # XXX FIXME BUG: Instead, we should do what twisted:#2671 wants.
        self.clock.callLater(0, self.sendExistingState)
        self.player = player
        return {"granularity": self.world.granularity,
                "identifier": identifier,
                "speed": player.speed,
                "x": v.x,
                "y": v.y,
                "z": v.z}
    Introduce.responder(introduce)


    def sendExistingState(self):
        """
        Send information about connected players.
        """
        self.sendExistingPlayers()


    def sendExistingPlayers(self):
        """
        Send L{NewPlayer} commands to this client for each existing L{Player} in
        the L{World}.
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
        v = player.getPosition()
        self.callRemote(SetDirectionOf,
                        identifier=self.identifierForPlayer(player),
                        direction=player.direction,
                        x=v.x, y=v.y, z=v.z,
                        orientation=player.orientation.y)

    # AMP responders
    def setMyDirection(self, direction, y):
        """
        Set the direction of the player of the client connected to this
        protocol.

        @param direction: The direction of movement, either forward, backward,
            left, right, or some non-opposing combination.

        @param y: The direction of forward, in degrees offset from movement
            along the z axis.
        """
        self.player.orientation.y = y
        self.player.setDirection(direction)
        v = self.player.getPosition()
        return {'x': v.x, 'y': v.y, 'z': v.z}
    SetMyDirection.responder(setMyDirection)


    def getTerrain(self, x, y, z):
        """
        The client would like terrain data from the given coordinates.
        """
        if x < 0 or y < 0 or z < 0:
            return {}
        voxels = self.world.terrain.voxels[x:x+64,y:y+8,z:z+64]
        self.callRemote(
            SetTerrain, x=x, y=y, z=z,
            voxels=voxels)
        return {}
    GetTerrain.responder(getTerrain)


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


    def connectionLost(self, reason):
        """
        Remove this connection's L{Player} from the L{World}.
        """
        self.world.removePlayer(self.player)



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
