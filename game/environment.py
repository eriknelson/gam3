
"""
Model code for the substrate the game world inhabits.
"""

from twisted.internet.task import Clock

class Environment(Clock):
    """
    Represent a number of global model parameters.

    @ivar scheduler: A callable like L{IReactorTime.callLater} which will be
    used to update the model time.

    @ivar granularity: The number of times to update the model time per second.
    """
    def __init__(self, granularity, scheduler):
        Clock.__init__(self)
        self.granularity = granularity
        self.scheduler = scheduler
        scheduler(1.0 / granularity, self._update)


    def _update(self):
        """
        Advance the simulation time by one second.
        """
        self.advance(1.0 / self.granularity)
        self.scheduler(1.0 / self.granularity, self._update)
