# -*- test-case-name: gam3.test.test_world -*-

r"""
  ____                 _____  __        __         _     _
 / ___| __ _ _ __ ___ |___ /  \ \      / /__  _ __| | __| |
| |  _ / _` | '_ ` _ \  |_ \   \ \ /\ / / _ \| '__| |/ _` |
| |_| | (_| | | | | | |___) |   \ V  V / (_) | |  | | (_| |
 \____|\__,_|_| |_| |_|____/     \_/\_/ \___/|_|  |_|\__,_|

"""

import random

from game.player import Player
from game.environment import SimulationTime

from epsilon.structlike import record


point = record('x y')

class World(SimulationTime):
    """
    All-encompassing model object for the state of a Gam3 game (until we get
    some distribution up ins).

    @ivar random: An object like L{random.Random}, used for entropic things.

    @ivar playerCreationRectangle: A two-tuple of points giving the
    southwestern and northeastern corners of a rectangle within which new
    players will be created.
    """
    def __init__(self, random=random, playerCreationRectangle=None,
                 granularity=None, scheduler=None):
        SimulationTime.__init__(self, granularity, scheduler)
        if playerCreationRectangle is None:
            playerCreationRectangle = point(-1, -1), point(1, 1)
        self.random = random
        self.playerCreationRectangle = playerCreationRectangle


    def createPlayer(self):
        """
        Make a new L{Player}.
        """
        sw, ne = self.playerCreationRectangle
        x = self.random.randrange(sw.x, ne.x)
        y = self.random.randrange(sw.y, ne.y)
        return Player((x, y), 2, lambda: 0)
