# -*- test-case-name: game.test.test_player -*-

from math import cos, sin, pi

from game.vector import Vector
from game.direction import FORWARD, BACKWARD, LEFT, RIGHT

class Player(object):
    """
    An object with a position.

    # XXX Call this class Character.

    @ivar _lastPosition: A L{Vector} instance, specifying the last computed
        position of player.

    @ivar seconds: A no-argument callable which returns the current time in
        seconds.

    @ivar direction: C{FORWARD}, C{LEFT}, the additive inverse of one of these,
        or the sum of any two non-additive-inverse of these four values,
        indicating the player's current direction of movement.

    @ivar speed: The distance which can be covered when the player is in motion
        (probably in something like cm/sec, if x and y are in cm).

    @ivar observers: A C{list} of objects notified about state changes of this
        object.
    """

    # XXX: This shouldn't be public. (make it a property without a setter?)
    direction = None

    def __init__(self, position, speed, seconds):
        assert isinstance(position, Vector)
        self._lastPosition = position
        self._lastDirectionChange = seconds()
        self.orientation = Vector(0, 0, 0)
        self.speed = speed
        self.seconds = seconds
        self.observers = []


    def setPosition(self, position):
        """
        Absolutely reposition this player.
        """
        assert isinstance(position, Vector)
        self._lastPosition = position
        self._lastDirectionChange = self.seconds()


    offset = {
        FORWARD: 0,
        BACKWARD: pi,
        LEFT: -pi / 2,
        RIGHT: pi / 2,
        FORWARD + LEFT: -pi / 4,
        FORWARD + RIGHT: pi / 4,
        BACKWARD + LEFT: -pi / 4 * 3,
        BACKWARD + RIGHT: pi / 4 * 3}

    def getPosition(self):
        """
        Retrieve the current position.

        @return: A L{Vector} giving the current position of the player.
        """
        v = self._lastPosition

        movement = self.direction
        if movement is None:
            return v

        now = self.seconds()
        elapsedTime = now - self._lastDirectionChange
        magnitude = elapsedTime * self.speed

        y = self.orientation.y / 180 * pi + self.offset[movement]
        direction = Vector(sin(y), 0, -cos(y))

        # Multiply by the magnitude to get the distance traveled and add to the
        # current position to get the new position. XXX This may be the wrong
        # time to update _lastPosition and _lastDirectionChange.
        self._lastPosition = v + direction * magnitude
        self._lastDirectionChange = self.seconds()

        return self._lastPosition


    def setDirection(self, direction):
        """
        Change the direction of movement of this player and notify any
        observers by invoking their C{directionChanged} method with no
        arguments.

        @param direction: One of the constants C{FORWARD}, C{BACKWARD}, etc, or
            C{None} if there is no movement.
        """
        self._lastPosition = self.getPosition()
        self._lastDirectionChange = self.seconds()
        self.direction = direction

        for observer in self.observers:
            observer.directionChanged(self)


    def turn(self, x, y):
        """
        Rotate the perspective by the given amount.
        """
        self.orientation.x += x
        self.orientation.y += y

        for observer in self.observers:
            observer.directionChanged(self)


    def addObserver(self, observer):
        """
        Add the given object to the list of those notified about state changes
        in this player.
        """
        self.observers.append(observer)
