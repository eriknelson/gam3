# -*- test-case-name: game.test.test_player -*-

class Player(object):
    """
    An object with a position.

    @ivar _lastPosition: A tuple of (x,y), specifying the last computed
    position of player.

    @ivar seconds: A no-argument callable which returns the current time in
    seconds.
    """

    def __init__(self, position, seconds):
        self._lastPosition = position
        self._lastDirectionChange = seconds()
        self.seconds = seconds
        self.direction = 0j


    def getPosition(self):
        """
        Retrieve the current position.

        @return: A two-tuple of ints giving the current position of the player.
        """
        x, y = self._lastPosition
        now = self.seconds()
        elapsedTime = now - self._lastDirectionChange
        s = self.direction * elapsedTime
        return x + s.imag, y + s.real


    def setDirection(self, direction):
        """
        Change the direction of movement of this player.

        @param direction: One of the constants C{NORTH}, C{SOUTH}, etc, or
        C{None} if there is no movement.
        """
        self._lastPosition = self.getPosition()
        self._lastDirectionChange = self.seconds()
        self.direction = direction
