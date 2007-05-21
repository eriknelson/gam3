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
        southwestern and northeastern corners of a rectangle within
        which new players will be created.

    @ivar observers: A C{list} of objects notified about state changes of this
        object.

    @ivar players: A C{list} of L{Player}s in this world.
    """
    def __init__(self, random=random, playerCreationRectangle=None,
                 granularity=None, platformClock=None):
        SimulationTime.__init__(self, granularity, platformClock)
        if playerCreationRectangle is None:
            playerCreationRectangle = point(-1, -1), point(200, 200)
        self.random = random
        self.playerCreationRectangle = playerCreationRectangle
        self.observers = []
        self.players = []


    def createPlayer(self):
        """
        Make a new L{Player}.
        """
        sw, ne = self.playerCreationRectangle
        x = self.random.randrange(sw.x, ne.x)
        y = self.random.randrange(sw.y, ne.y)
        player = Player((x, y), 100, lambda: 0)
        for observer in self.observers:
            observer.playerCreated(player)
        self.players.append(player)
        return player


    def addObserver(self, observer):
        """
        Add the given object to the list of those notified about state changes
        in this world.
        """
        self.observers.append(observer)


    def getPlayers(self):
        """
        Return an iterator of all L{Player}s in this L{World}.
        """
        return iter(self.players)

