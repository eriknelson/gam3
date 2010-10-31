# -*- test-case-name: game.test.test_network -*-

"""
Network support for Game.
"""

from struct import pack, unpack

from twisted.protocols.amp import (
    AMP, AmpList, Command, Integer, Float, String, Argument)

from game.environment import Environment
from game.vec3 import vec3

class Direction(Argument):
    """
    Encode L{complex} objects as two bytes.
    """
    def toString(self, direction):
        """
        Convert the direction to two bytes.
        """
        if direction is not None:
            x = direction.real
            y = direction.imag
        else:
            x = y = 0
        return pack("bb", x, y)


    def fromString(self, encodedDirection):
        """
        Convert the direction from bytes.
        """
        direction = complex(*unpack("bb", encodedDirection))
        if direction == 0j:
            direction = None
        return direction



class Introduce(Command):
    """
    Client greeting message used to retrieve initial model state.
    """
    response = [('identifier', Integer()),
                ('granularity', Integer()),
                ('speed', Integer()),
                ('x', Float()),
                ('y', Float()),
                ('z', Float())]



Terrain = String

class SetTerrain(Command):
    """
    Specify the type of terrain at one or more positions.
    """
    arguments = [('terrain', AmpList([
                    ('x', Integer()),
                    ('y', Integer()),
                    ('z', Integer()),
                    ('type', Terrain())]))]






class NewPlayer(Command):
    """
    Notify someone that a L{Player} with the given C{identifier} is at
    the given position.

    @param identifier: The unique identifier for the player whose
        position will, be set.
    @param x: The x position.
    @param y: The y position.
    """

    arguments = [('identifier', Integer()),
                 ('x', Float()),
                 ('y', Float()),
                 ('z', Float()),
                 ('speed', Integer())]


class RemovePlayer(Command):
    """
    Notify someone that a L{Player} with the given C{identifier} has
    been removed.

    @param identifier: The unique identifier for the player whose position will
        be set.
    """
    arguments = [('identifier', Integer())]



class SetMyDirection(Command):
    """
    Set the direction of my L{Player}.

    This is a client to server command.

    @type direction: L{Direction}
    @param direction: The new direction.

    @param y: The direction the player is facing.
    @type y: L{Float}

    @return x: The x coordinate of the player at the time the server received
        the Command.
    @return y: Same as x, save for the y coordinate.
    @return z: Same as x, save for the z coordinate.
    """

    arguments = [('direction', Direction()),
                 ('y', Float())]

    response = [('x', Float()),
                ('y', Float()),
                ('z', Float())]



class SetDirectionOf(Command):
    """
    Set the position, orientation, and direction of a L{Player}.

    This is a server to client command which indicates the new direction and
    position of a L{Player}.

    @param identifier: The unique identifier for the player whose position will
        be set.
    @type direction: L{Direction}.
    @param direction: The new direction of the player.
    @param x: The x coordinate at the time of change in direction.
    @param y: The y coordinate at the time of change in direction.
    @param z: The z coordinate at the time of change in direction.
    @param orientation: The y angle of the orientation of the player.
    """

    arguments = [('identifier', Integer()),
                 ('direction', Direction()),
                 ('x', Float()),
                 ('y', Float()),
                 ('z', Float()),
                 ('orientation', Float())]


class NetworkController(AMP):
    """
    A controller which responds to AMP commands to make state changes to local
    model objects.

    @ivar modelObjects: A C{dict} mapping identifiers to model objects.

    @ivar clock: A provider of L{IReactorTime} which will be used to
        update the model time.
    """

    environment = None

    def __init__(self, clock):
        self.modelObjects = {}
        self.clock = clock


    def addModelObject(self, identifier, modelObject):
        """
        Associate a network identifier with a model object.
        """
        self.modelObjects[identifier] = modelObject
        modelObject.addObserver(self)


    def directionChanged(self, modelObject):
        """
        Notify the network that a local model object changed direction.

        @param modelObject: The L{Player} whose direction has changed.
        """
        d = self.callRemote(
            SetMyDirection,
            direction=modelObject.direction, y=modelObject.orientation.y)
        d.addCallback(self._gotNewPosition, modelObject)
        # XXX Add an errback


    def _gotNewPosition(self, position, player):
        """
        Update a L{Player}'s position based on new data from the server.

        @param player: The L{Player} whose position to change.
        @param position: Dict with C{x} and C{y} keys, whose values should be
        integers specifying position.
        """
        player.setPosition(vec3(position['x'], position['y'], position['z']))


    def createInitialPlayer(self, environment, identifier, position,
                            speed):
        """
        Create this client's player as the initial player in the given
        environment and add it to the model object mapping.
        """
        player = environment.createPlayer(position, speed)
        environment.setInitialPlayer(player)
        self.addModelObject(identifier, player)


    def introduce(self):
        """
        Greet the server and register the player model object which belongs to
        this client and remember the identifier with which it responds.
        """
        d = self.callRemote(Introduce)
        def cbIntroduce(box):
            granularity = box['granularity']
            position = vec3(box['x'], box['y'], box['z'])
            speed = box['speed']
            self.environment = Environment(granularity, self.clock)
            self.createInitialPlayer(
                self.environment, box['identifier'], position,
                speed)
            return self.environment
        d.addCallback(cbIntroduce)
        return d


    def objectByIdentifier(self, identifier):
        """
        Look up a pre-existing model object by its network identifier.

        @type identifier: C{int}

        @raise KeyError: If no existing model object has the given identifier.
        """
        return self.modelObjects[identifier]


    def identifierByObject(self, modelObject):
        """
        Look up the network identifier for a given model object.

        @raise ValueError: If no network identifier is associated with the
            given model object.

        @rtype: L{int}
        """
        for identifier, object in self.modelObjects.iteritems():
            if object is modelObject:
                return identifier
        raise ValueError("identifierByObject passed unknown model objects")


    def setDirectionOf(self, identifier, direction, x, y, z, orientation):
        """
        Set the direction of a local model object.

        @type identifier: L{int}
        @type direction: One of the L{game.direction} direction constants

        @see: L{SetDirectionOf}
        """
        player = self.objectByIdentifier(identifier)
        player.setDirection(direction)
        player.setPosition(vec3(x, y, z))
        player.orientation.y = orientation
        return {}
    SetDirectionOf.responder(setDirectionOf)


    def newPlayer(self, identifier, x, y, z, speed):
        """
        Add a new L{Player} object to the L{Environment} and start
        tracking its identifier on the network.

        @param identifier: The network-level identifier of the player.
        @param x: The x position of the new L{Player}.
        @param y: The y position of the new L{Player}.
        @param z: The z position of the new L{Player}.
        """
        player = self.environment.createPlayer(vec3(x, y, z), speed)
        self.modelObjects[identifier] = player
        return {}
    NewPlayer.responder(newPlayer)


    def removePlayer(self, identifier):
        """
        Remove an existing L{Player} object from the L{Environment}
        and stop tracking its identifier on the network.

        @param identifier: The network-level identifier of the player.
        """
        self.environment.removePlayer(self.objectByIdentifier(identifier))
        del self.modelObjects[identifier]
        return {}
    RemovePlayer.responder(removePlayer)


    def setTerrain(self, terrain):
        """
        Add new terrain information to the environment.

        @param terrain: A sequence of mappings with C{"type"}, C{"x"} and C{"y"}
            keys.
        """
        for info in terrain:
            self.environment.terrain[
                info["x"], info["y"], info["z"]] = info["type"]
        return {}
    SetTerrain.responder(setTerrain)
