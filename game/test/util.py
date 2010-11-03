# -*- test-case-name: game.test -*-

"""
Assorted utility code for tests.
"""

from game.player import Player


class PlayerCreationMixin:
    """
    Provides convenient Player creation functionality.
    """
    # Not 0 to avoid stupid arithmetic errors.
    currentSeconds = 15

    def makePlayer(self, position, speed=1):
        """
        Create a new L{Player} at the given position with a model time function
        which is controlled by C{self.currentSeconds}.
        """
        return Player(
            position,
            speed=speed,
            seconds=lambda: self.currentSeconds)


    def advanceTime(self, amount):
        """
        Advance the clock by the given number of seconds.
        """
        self.currentSeconds += amount



class PlayerVisibilityObserver(object):
    """
    Record player creation notifications.

    @ivar createdPlayers: A list of players passed to L{playerCreated} calls.
    @ivar removedPlayers: A list of players passed to L{playerRemoved} calls.
    """
    def __init__(self):
        self.createdPlayers = []
        self.removedPlayers = []


    def playerCreated(self, player):
        """
        Record a player creation.
        """
        self.createdPlayers.append(player)


    def playerRemoved(self, player):
        """
        Record a player removal.
        """
        self.removedPlayers.append(player)



class MockSurface(object):
    """
    An object that is supposed to look like L{pygame.Surface}.

    @ivar size: A two-tuple of ints giving the pixel dimensions of this image.

    @ivar label: A C{str} identifying this surface to a human.
    """
    def __init__(self, label, size, depth=None):
        self.label = label
        self.size = size
