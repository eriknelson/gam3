# -*- test-case-name: game.test.test_environment -*-

"""
Model code for the substrate the game world inhabits.
"""

from twisted.internet.task import Clock

from game.player import Player


class Environment(Clock):
    """
    The part of The World which is visible to a client.

    @ivar _platformCallLater: A callable like L{IReactorTime.callLater} which
    will be used to update the model time.

    @ivar granularity: The number of times to update the model time
        per second. That is, the number of "instants" per
        second. e.g., specifying 2 would make calls to seconds()
        return 0 for 0.5 seconds, then 0.5 for 0.5 seconds, then 1 for
        0.5 seconds, and so on. This number directly represents the
        B{model} frames per second.

    @ivar _call: The result of the latest call to C{scheduler}.

    @ivar observers: A C{list} of objects notified about state changes of this
    object.

    @ivar initialPlayer: C{None} until an initial player is set, then whatever
    L{Player} it is set to.
    """
    _call = None
    initialPlayer = None

    def __init__(self, granularity, platformCallLater):
        Clock.__init__(self)
        self.granularity = granularity
        self._platformCallLater = platformCallLater
        self.observers = []


    def setInitialPlayer(self, player):
        """
        Set the initial player to the given player.
        """
        self.initialPlayer = player


    def _update(self):
        """
        Advance the simulation time by one second.
        """
        self.advance(1.0 / self.granularity)
        self.start()


    def start(self):
        """
        Start the simulated advancement of time.
        """
        self._call = self._platformCallLater(1.0 / self.granularity,
                                             self._update)


    def stop(self):
        """
        Stop the simulated advancement of time. Clean up all pending calls.
        """
        self._call.cancel()


    def addObserver(self, observer):
        """
        Add the given object to the list of those notified about state changes
        in this environment.
        """
        self.observers.append(observer)


    def createPlayer(self, position, speed):
        """
        Make a new player with the given parameters.

        @type position: two-tuple of numbers
        @param position: Where the newly created player is.

        @type speed: number
        @param speed: How fast can newly created player go?

        @return: The new L{Player}
        """
        player = Player(position, speed, self.seconds)
        for observer in self.observers:
            observer.playerCreated(player)
        return player

