# -*- test-case-name: game.test.test_network -*-

"""
Network support for Game.
"""

from struct import pack, unpack

from twisted.protocols.amp import AMP, Command, Integer, Argument


class Direction(Argument):
    """
    Encode L{complex} objects as two bytes.
    """
    def toString(self, direction):
        """
        Convert the direction to two bytes.
        """
        return pack("bb", direction.real, direction.imag)


    def fromString(self, encodedDirection):
        """
        Convert the direction from bytes.
        """
        return complex(*unpack("bb", encodedDirection))



class Introduce(Command):
    """
    Client greeting message used to retrieve initial model state.
    """


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
    """
    def __init__(self):
        self.modelObjects = {}


    def addModelObject(self, identifier, modelObject):
        """
        Associate a network identifier with a model object.
        """
        self.modelObjects[identifier] = modelObject
        modelObject.addObserver(lambda: self.modelObjectDirectionChanged(modelObject))


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

        @raise KeyError:

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
