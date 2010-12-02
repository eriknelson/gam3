"""
Functionality related to the shape of the world.
"""

from numpy import array, zeros

from game.vector import Vector

EMPTY, GRASS, MOUNTAIN, DESERT, WATER = range(5)

TOP, FRONT, BOTTOM, BACK, LEFT, RIGHT = range(6)
FACES = (TOP, FRONT, BOTTOM, BACK, LEFT, RIGHT)
NEIGHBORS = {
    TOP: (0, 1, 0),
    FRONT: (0, 0, 1),
    BOTTOM: (0, -1, 0),
    BACK: (0, 0, -1),
    LEFT: (-1, 0, 0),
    RIGHT: (1, 0, 0)}


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
        self.voxels = zeros((1, 1, 1), 'b')
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
            data = self.voxels.copy()
            self.voxels.resize((
                    max(existing[0], new[0]),
                    max(existing[1], new[1]),
                    max(existing[2], new[2])))
            self.voxels[:existing[0],:existing[1],:existing[2]] = data

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


_cube = {
    3: (0, 0, 0),  # Front
    4: (1, 0, 0),
    8: (0, 1, 0),
    7: (1, 1, 0),

    1: (0, 0, 1),  # Back
    2: (1, 0, 1),
    5: (0, 1, 1),
    6: (1, 1, 1),
    }

def _s(n):
    return _cube[n] + (0, 0)

_top = array(map(_s, [7, 8, 5, 7, 6, 5]))
_front = array(map(_s, [5, 1, 2, 5, 6, 2]))
_bottom = array(map(_s, [1, 3, 4, 1, 2, 4]))
_back = array(map(_s, [3, 8, 7, 3, 4, 7]))
_left = array(map(_s, [3, 1, 5, 3, 8, 5]))
_right = array(map(_s, [2, 4, 7, 2, 6, 7]))


class SurfaceMesh(object):
    """
    A terrain change observer which constructs a surface mesh of the terrain
    from prism updates.

    @ivar surface: A triangle mesh of the exposed terrain which should be
        rendered.  Each element of the array contains position and texture
        information about one vertex of one triangle, as (x, y, z, tx, ty, tz).

    @ivar important: An index into C{surface} indicating the end of the useful
        elements.  Elements beyond this are garbage to be ignored.

    @ivar _voxelToSurface: A dictionary mapping the world position of a voxel to
        a pair indicating a slice of C{surface} which is displaying a face of
        that voxel.

    @ivar _textureOffsets: A dictionary mapping terrain types to arrays of
        texture coordinate (x, y) pairs.  These coordinates are the top-left
        position of the texture for that terrain type.

    @ivar _textureExtent: A float indicating the distance between the sides of
        the textures.
    """
    def __init__(self, terrain, textureOffsets=None, textureExtent=None):
        self._terrain = terrain
        self.surface = zeros((1000000, 5), dtype='f')
        self.important = 0
        self._voxelToSurface = {}
        self._textureOffsets = textureOffsets
        self._textureExtent = textureExtent

        toptex = array([
                [0, 0, 0, textureExtent, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, textureExtent],
                [0, 0, 0, textureExtent, 0],
                [0, 0, 0, textureExtent, textureExtent],
                [0, 0, 0, 0, textureExtent]
                ])

        fronttex = toptex
        bottomtex = toptex
        backtex = toptex
        lefttex = toptex
        righttex = toptex

        self._faces = {
            TOP: (_top, toptex),
            FRONT: (_front, fronttex),
            BOTTOM: (_bottom, bottomtex),
            BACK: (_back, backtex),
            LEFT: (_left, lefttex),
            RIGHT: (_right, righttex),
            }

        # Do this last
        self.changed(Vector(0, 0, 0), Vector(*self._terrain.voxels.shape))


    def _makeFace(self, face, textureType, x, y, z):
        s, t = self._textureOffsets[textureType]
        offset = [x, y, z, s, t]
        pos, tex = self._faces[face]
        return pos + tex + offset


    def _append(self, key, vertices):
        pos = self.important
        # XXX Bounds checking needed here.
        self.surface[pos:pos + len(vertices)] = vertices
        self._voxelToSurface[key] = (pos, len(vertices))
        self.important += len(vertices)


    def _compact(self, x, y, z, face, start, length):
        # Find the voxel that owns the vertices at the end of the surface mesh
        # array.
        mx, my, mz = self.surface[self.important - 6][:3]

        # Use knowledge about the location of the first vertex of the first
        # triangle of the top face to find the voxel.
        mx -= 1
        my -= 1

        # If this fails we are screwed.
        assert self._voxelToSurface[mx, my, mz] == (self.important - 6, 6)
        self._voxelToSurface[mx, my, mz] = (start, length)
        self.surface[start:length] = self.surface[self.important - 6:self.important]
        self.important -= 6


    def _removeVoxel(self, x, y, z):
        for face in FACES:
            key = (x, y, z, face)
            if key in self._voxelToSurface:
                begin, length = self._voxelToSurface.pop(key)
                if begin + length == self.important:
                    # If these voxels are at the end, just reduce
                    # the top marker.
                    self.important -= length
                else:
                    # Otherwise move some vertices from the end to
                    # overwrite these.
                    self._compact(x, y, z, face, begin, length)


    def _exposed(self, x, y, z, face):
        voxels = self._terrain.voxels
        mx, my, mz = voxels.shape

        dx, dy, dz = NEIGHBORS[face]
        x += dx
        y += dy
        z += dz

        return (
            x < 0 or y < 0 or z < 0 or
            x >= mx or y >= my or z >= mz or
            voxels[x, y, z] == EMPTY)


    def _addVoxel(self, x, y, z):
        for face in FACES:
            key = (x, y, z, face)
            if key not in self._voxelToSurface:
                # If there's nothing there already, check to see if it is
                # exposed.
                if self._exposed(x, y, z, face):
                    # If the neighbor is empty, it is exposed, add it.
                    self._append(
                        key,
                        self._makeFace(
                            face,
                            self._terrain.voxels[x, y, z], x, y, z))


    def changed(self, position, shape):
        """
        Examine the terrain type at every changed voxel and determine if there
        are any exposed faces.  If so, update the surface mesh array.
        """
        voxels = self._terrain.voxels

        # Visit each voxel in the changed region plus one in each direction
        # (XXX) and re-determine if it should now be part of the surface mesh.
        for x in range(int(position.x), int(position.x + shape.x)):
            for y in range(int(position.y), int(position.y + shape.y)):
                for z in range(int(position.z), int(position.z + shape.z)):

                    if voxels[x, y, z] == EMPTY:
                        self._removeVoxel(x, y, z)
                    else:
                        self._addVoxel(x, y, z)
