# -*- test-case-name: game.test.test_network -*-

"""
Network support for Game.
"""

from struct import pack, unpack

from twisted.protocols.amp import AMP, Command, Integer, Argument

from game.player import Player
from game.environment import Environment


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
                ('x', Integer()),
                ('y', Integer())]



class SetPositionOf(Command):
    """
    Set the position of a L{Player}.

    @param identifier: The unique identifier for the player whose position will
        be set.
    @param x: The x position.
    @param y: The y position.
    """

    arguments = [('identifier', Integer()),
                 ('x', Integer()),
                 ('y', Integer())]



class NewPlayer(Command):
    """
    Notify someone that a L{Player} of the given C{identifier} is at
    the given position.

    @param identifier: The unique identifier for the player whose position will
        be set.
    @param x: The x position.
    @param y: The y position.
    """

    arguments = [('identifier', Integer()),
                 ('x', Integer()),
                 ('y', Integer())]




class SetDirectionOf(Command):
    """
    Set the direction of a L{Player}.

    @param identifier: The unique identifier for the player whose position will
        be set.
    @type direction: L{Direction}.
    @param direction: The new direction of the player.
    """

    arguments = [('identifier', Integer()),
                 ('direction', Direction())]


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
        self.callRemote(
            SetDirectionOf,
            identifier=self.identifierByObject(modelObject),
            direction=modelObject.direction)


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
            position = box['x'], box['y']
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


    def setPositionOf(self, identifier, x, y):
        """
        Set the position of a local model object.

        @type identifier: L{int}
        @type x: L{int}
        @type y: L{int}

        @see SetPosition
        """
        self.objectByIdentifier(identifier).setPosition((x, y))
        return {}
    SetPositionOf.responder(setPositionOf)


    def setDirectionOf(self, identifier, direction):
        """
        Set the direction of a local model object.

        @type identifier: L{int}
        @type direction: One of the L{game.direction} direction constants

        @see SetDirectionOf
        """
        self.objectByIdentifier(identifier).setDirection(direction)
        return {}
    SetDirectionOf.responder(setDirectionOf)
