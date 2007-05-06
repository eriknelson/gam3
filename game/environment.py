"""
Model code for the substrate the game world inhabits.
"""

from twisted.internet.task import Clock

class Environment(Clock):
    """
    Represent a number of global model parameters.

    @ivar scheduler: A callable like L{IReactorTime.callLater} which will be
    used to update the model time.

    @ivar granularity: The number of times to update the model time
        per second. That is, the number of "instants" per
        second. e.g., specifying 2 would make calls to seconds()
        return 0 for 0.5 seconds, then 0.5 for 0.5 seconds, then 1 for
        0.5 seconds, and so on. This number directly represents the
        B{model} frames per second.

    @ivar _call: The result of the latest call to C{scheduler}.
    """
    def __init__(self, granularity, scheduler):
        Clock.__init__(self)
        self.granularity = granularity
        self.scheduler = scheduler
        self._call = scheduler(1.0 / granularity, self._update)


    def _update(self):
        """
        Advance the simulation time by one second.
        """
        self.advance(1.0 / self.granularity)
        self._call = self.scheduler(1.0 / self.granularity, self._update)

    def stop(self):
        """
        Stop the simulated advancement of time. Clean up all pending calls.
        """
        self._call.cancel()
