# -*- test-case-name: game.test.test_player -*-

class Player(object):
    """
    An object with a position.

    @ivar _lastPosition: A tuple of (x,y), specifying the last computed
    position of player.

    @ivar seconds: A no-argument callable which returns the current time in
    seconds.

    @ivar direction: C{NORTH}, C{EAST} the additive inverse of one of these, or
    the sum of any two non-additive-inverse of these four values.

    @ivar speed: The distance which can be covered when the player
    is in motion (probably in something like cm/sec, if x and y are in cm.

    @ivar observers: A C{list} of objects notified about state changes of this
    object.
    """

    # XXX: This shouldn't be public. (make it a property without a setter?)
    direction = None

    def __init__(self, position, speed, seconds):
        self._lastPosition = position
        self._lastDirectionChange = seconds()
        self.speed = speed
        self.seconds = seconds
        self.observers = []


    def setPosition(self, position):
        """
        Absolutely reposition this player.
        """
        self._lastPosition = position
        self._lastDirectionChange = self.seconds()


    def getPosition(self):
        """
        Retrieve the current position.

        @return: A two-tuple of ints giving the current position of the player.
        """
        x, y = self._lastPosition
        now = self.seconds()
        elapsedTime = now - self._lastDirectionChange
        s = (self.direction or 0j) * elapsedTime * self.speed
        return int(x + s.imag), int(y + s.real)


    def setDirection(self, direction):
        """
        Change the direction of movement of this player and notify any
        observers by invoking their C{directionChanged} method with no
        arguments.

        @param direction: One of the constants C{NORTH}, C{SOUTH}, etc, or
        C{None} if there is no movement.
        """
        self._lastPosition = self.getPosition()
        self._lastDirectionChange = self.seconds()
        self.direction = direction

        for observer in self.observers:
            observer.directionChanged(self)


    def addObserver(self, observer):
        """
        Add the given object to the list of those notified about state changes
        in this player.
        """
        self.observers.append(observer)
