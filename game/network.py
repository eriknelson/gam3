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



class SetPosition(Command):
    """
    Set the position of a L{Player}.

    @param x: The x position.
    @param y: The y position.
    """

    arguments = [('x', Integer()),
                 ('y', Integer())]


class SetDirection(Command):
    """
    Set the direction of a L{Player}.

    @type direction: L{Direction}.
    @param direction: The new direction of the player.
    """

    arguments = [('direction', Direction())]


class NetworkPlayerController(AMP):
    """
    A controller which responds to AMP commands to control the L{Player}.

    @ivar player: The L{Player} object to control.
    """
    def __init__(self, player):
        self.player = player


    def setPosition(self, x, y):
        """
        Set the position of C{self.player}.

        @type x: L{int}
        @type y: L{int}

        @see SetPosition
        """
        self.player.setPosition((x, y))
        return {}
    SetPosition.responder(setPosition)


    def setDirection(self, direction):
        """
        @type direction: One of the L{game.direction} direction constants

        @see SetDirection
        """
        self.player.setDirection(direction)
        return {}
    SetDirection.responder(setDirection)


