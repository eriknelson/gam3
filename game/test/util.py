
from game.player import Player


class PlayerCreationMixin:
    """
    Provides convenient Player creation functionality.
    """
    # Not 0 to avoid stupid arithmetic errors.
    currentSeconds = 15

    def makePlayer(self, position, movementVelocity=1):
        """
        Create a new L{Player} at the given position with a model time function
        which is controlled by C{self.currentSeconds}.
        """
        return Player(
            position,
            movementVelocity=movementVelocity,
            seconds=lambda: self.currentSeconds)


    def advanceTime(self, amount):
        """
        Advance the clock by the given number of seconds.
        """
        self.currentSeconds += amount



class PlayerCreationObserver(object):
    """
    Record player creation notifications.

    @ivar createdPlayers: A list of two-tuples giving the arguments to
    L{playerCreated} calls.
    """
    def __init__(self):
        self.createdPlayers = []


    def playerCreated(self, player, voluble):
        """
        Record a player creation.
        """
        self.createdPlayers.append((player, voluble))
