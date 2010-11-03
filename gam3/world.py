# -*- test-case-name: gam3.test.test_world -*-

r"""
  ____                 _____  __        __         _     _
 / ___| __ _ _ __ ___ |___ /  \ \      / /__  _ __| | __| |
| |  _ / _` | '_ ` _ \  |_ \   \ \ /\ / / _ \| '__| |/ _` |
| |_| | (_| | | | | | |___) |   \ V  V / (_) | |  | | (_| |
 \____|\__,_|_| |_| |_|____/     \_/\_/ \___/|_|  |_|\__,_|

"""

import random

from twisted.application.service import Service

from game.player import Player
from game.environment import SimulationTime

from epsilon.structlike import record


TCP_SERVICE_NAME = 'tcp-service-name'
GAM3_SERVICE_NAME = 'gam3-service-name'

point = record('x y')

class World(SimulationTime):
    """
    All-encompassing model object for the state of a Gam3 game (until we get
    some distribution up ins).

    @ivar random: An object like L{random.Random}, used for entropic things.

    @ivar playerCreationRectangle: A two-tuple of points giving the southwestern
        (lower bounds on x and y axis) and northeastern (upper bounds on x and y
        axis) corners of a rectangle within which new players will be created.

    @ivar observers: A C{list} of objects notified about state changes of this
        object.

    @ivar players: A C{list} of L{Player}s in this world.

    @ivar terrain: A C{dict} mapping x, y coordinate tuples to a terrain type
        for that location.
    """
    def __init__(self, random=random, playerCreationRectangle=None,
                 granularity=1, platformClock=None):
        SimulationTime.__init__(self, granularity, platformClock)
        if playerCreationRectangle is None:
            playerCreationRectangle = point(-1, -1), point(200, 200)
        self.random = random
        self.playerCreationRectangle = playerCreationRectangle
        self.observers = []
        self.players = []
        self.terrain = {}


    def createPlayer(self):
        """
        Make a new L{Player}.
        """
        sw, ne = self.playerCreationRectangle
        x = self.random.randrange(sw.x, ne.x)
        y = self.random.randrange(sw.y, ne.y)
        player = Player((x, y), 100, self.seconds)
        for observer in self.observers:
            observer.playerCreated(player)
        self.players.append(player)
        return player


    def removePlayer(self, player):
        """
        Stop tracking the given L{Player} and notify observers via the
        C{playerRemoved} method.
        """
        self.players.remove(player)
        for observer in self.observers:
            observer.playerRemoved(player)


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



class Gam3Service(Service):
    """
    An L{IService<twisted.application.service.IService>} which starts and stops
    simulation time on a L{World}.

    @ivar world: The L{World} to start and stop.
    """
    def __init__(self, world):
        self.world = world


    def startService(self):
        """
        Start simulation time on the wrapped world.
        """
        self.world.start()


    def stopService(self):
        """
        Stop simulation time on the wrapped world.
        """
        self.world.stop()
