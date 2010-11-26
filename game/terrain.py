"""
Functionality related to the shape of the world.
"""

from numpy import zeros

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
