
"""
Functionality related to the shape of the world.
"""

from numpy import zeros

from game.terrain import GRASS, MOUNTAIN, DESERT, WATER


def loadTerrainFromString(map):
    """
    Load terrain from the given map string.  The string represents two
    dimensional terrain data with x varying fastest.

    @return: A matrix of the terrain data.
    """
    types = {'G': GRASS, 'M': MOUNTAIN, 'D': DESERT, 'W': WATER}
    map = map.strip()
    data = map.splitlines()
    voxels = zeros((len(map) / len(data), 1, len(data)), 'b')
    for z, line in enumerate(map.strip().splitlines()):
        for x, ch in enumerate(line):
            voxels[x, 0, z] = types[ch]
    return voxels


