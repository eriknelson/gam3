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



class MockWindow(object):
    """
    An object that is supposed to look like L{Window}.

    @ivar draws: A list of two-tuples giving the arguments to all
    calls to the C{draw} method.

    @ivar dirtied: An integer giving the number of calls to the C{dirty}
    method.
    """
    def __init__(self):
        self.draws = []
        self.dirtied = 0


    def draw(self, image, position):
        """
        Record an attempt to render an image at a particular location.
        """
        self.draws.append((image, position))


    def dirty(self):
        """
        Record an attempt to dirty the window.
        """
        self.dirtied += 1



class MockSurface(object):
    """
    An object that is supposed to look like L{pygame.Surface}.

    @ivar size: A two-tuple of ints giving the pixel dimensions of this image.

    @ivar blits: A list of two-tuples giving the arguments to all
        calls to the C{blit} method.

    @ivar fills: A list of three-tuples giving the colors passed to
        the C{fill} method.
    """
    def __init__(self, label, size, depth=None):
        self.label = label
        self.size = size
        self.depth = depth
        self.blits = []
        self.fills = []


    def get_bitsize(self):
        """
        Return the color depth of this surface.
        """
        return self.depth


    def blit(self, surface, position):
        """
        Record an attempt to blit another surface onto this one.
        """
        self.blits.append((surface, position))


    def fill(self, color):
        """
        Record an attempt to fill the entire surface with a particular color.
        """
        self.fills.append(color)


    def get_size(self):
        """
        Return the size of this image.
        """
        return self.size


    def convert(self, depth):
        """
        Create a new L{MockImage} with the indicated depth.
        """
        return MockSurface(self.label, self.size, depth)
