"""
Functionality related to the shape of the world.
"""

from numpy import array, zeros

from game.vector import Vector

EMPTY, GRASS, MOUNTAIN, DESERT, WATER = range(5)

def loadTerrainFromString(map):
    """
    Load terrain from the given map string.  The string represents two
    dimensional terrain data with x varying fastest.

    @return: A matrix of the terrain data.
    """
    types = {'_': EMPTY, 'G': GRASS, 'M': MOUNTAIN, 'D': DESERT, 'W': WATER}
    map = map.strip()
    data = list(plane.splitlines() for plane in map.split('\n\n'))
    shape = (len(data[0][0]), len(data), len(data[0]))
    voxels = zeros(shape, 'b')
    for y, plane in enumerate(data):
        for z, line in enumerate(plane):
            for x, ch in enumerate(line):
                voxels[x, shape[1] - y - 1, z] = types[ch]
    return voxels


class Terrain(object):
    """
    @ivar voxels:
    @type voxels: L{numpy.array}

    @ivar _observers:
    @type _observers: C{list}
    """
    def __init__(self):
        self.voxels = array([EMPTY], 'b', ndmin=3)
        # XXX Seriously why do I implement this eleven times a day?
        self._observers = []


    def dict(self):
        """
        Return all voxel data as a dictionary.
        """
        return dict(((x, y, z), self.voxels[x, y, z])
                    for x in range(self.voxels.shape[0])
                    for y in range(self.voxels.shape[1])
                    for z in range(self.voxels.shape[2])
                    if self.voxels[x, y, z] != EMPTY)


    def set(self, x, y, z, voxels):
        """
        Replace a chunk of voxels, starting from C{(x, y, z)}.
        """
        existing = array(self.voxels.shape)
        new = array(voxels.shape)
        new[0] += x
        new[1] += y
        new[2] += z

        if new[0] > existing[0] or new[1] > existing[1] or new[2] > existing[2]:
            terrain = array([[[]]], 'b', ndmin=3)
            terrain.resize((
                    max(existing[0], new[0]),
                    max(existing[1], new[1]),
                    max(existing[2], new[2])))
            terrain[:existing[0],:existing[1],:existing[2]] = self.voxels
            self.voxels = terrain

        self.voxels[x:,y:,z:] = voxels
        self._notify(Vector(x, y, z), Vector(*voxels.shape))


    def _notify(self, position, shape):
        """
        Call all observers with the change information.
        """
        for obs in self._observers:
            obs(position, shape)


    def addObserver(self, observer):
        """
        Whenever this terrain changes, notify C{observer}.

        @param observer: A callable which will be invoked with a position
            L{Vector} and a shape L{Vector}.
        """
        self._observers.append(observer)

