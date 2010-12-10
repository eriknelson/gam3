"""
Functionality related to the shape of the world.
"""

from numpy import array, zeros, empty

from twisted.python.log import err

from game.vector import Vector

EMPTY, GRASS, MOUNTAIN, DESERT, WATER, UNKNOWN = range(6)

TOP, FRONT, BOTTOM, BACK, LEFT, RIGHT = range(6)
FACES = (TOP, FRONT, BOTTOM, BACK, LEFT, RIGHT)
NEIGHBORS = {
    TOP: (0, 1, 0, BOTTOM),
    FRONT: (0, 0, 1, BACK),
    BOTTOM: (0, -1, 0, TOP),
    BACK: (0, 0, -1, FRONT),
    LEFT: (-1, 0, 0, RIGHT),
    RIGHT: (1, 0, 0, LEFT)}


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
        self.voxels = array([[[UNKNOWN]]], ndmin=3, dtype='b')
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
                    if self.voxels[x, y, z] not in (EMPTY, UNKNOWN))


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
            self.voxels = empty((
                    max(existing[0], new[0]),
                    max(existing[1], new[1]),
                    max(existing[2], new[2])), 'b')
            self.voxels.fill(UNKNOWN)
            self.voxels[:existing[0],:existing[1],:existing[2]] = data

        self.voxels[x:new[0],y:new[1],z:new[2]] = voxels
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

_top = array(map(_s, [7, 8, 5, 7, 6, 5]), 'f')
_front = array(map(_s, [5, 1, 2, 5, 6, 2]), 'f')
_bottom = array(map(_s, [1, 3, 4, 1, 2, 4]), 'f')
_back = array(map(_s, [3, 8, 7, 3, 4, 7]), 'f')
_left = array(map(_s, [3, 1, 5, 3, 8, 5]), 'f')
_right = array(map(_s, [2, 4, 7, 2, 6, 7]), 'f')


class SurfaceMesh(object):
    """
    A terrain change observer which constructs a surface mesh of the terrain
    from prism updates.

    @ivar _surfaceFactory: A callable which will return a new array with shape
        (N, 5) for some fairly large N.  Whenever an array is completely filled
        with vertices, this is called to get a new one.

    @ivar _surfaces: A list of two-tuples of arrays holding the triangle mesh of
        the exposed terrain which should be rendered and an index giving the
        first unused index in the corresponding array.  Each element of the
        array contains position and texture information about one vertex of one
        triangle, as (x, y, z, tx, ty).

    @ivar _voxelToSurface: A dictionary mapping the world position of a voxel to
        a pair indicating a slice of C{surface} which is displaying a face of
        that voxel.

    @ivar _textureOffsets: A dictionary mapping terrain types to arrays of
        texture coordinate (x, y) pairs.  These coordinates are the top-left
        position of the texture for that terrain type.

    @ivar _textureExtent: A float indicating the distance between the sides of
        the textures.
    """
    def __init__(self, terrain, surfaceFactory, textureOffsets=None,
                 textureExtent=None):
        self._terrain = terrain
        self._surfaceFactory = surfaceFactory
        self._surfaces = [surfaceFactory()]
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
                ], 'f')

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
        # First do a copying operation so neither of the base data arrays
        # changes.
        result = pos + tex
        # Next do an in-place operation, for performance and to retain the
        # dtype.
        result += offset
        return result


    def _append(self, key, vertices):
        assert key not in self._voxelToSurface
        pos = self._surfaces[-1][2]
        # XXX Bounds checking needed here.
        self._surfaces[-1][0][pos:pos + len(vertices)] = vertices
        self._voxelToSurface[key] = (pos, len(vertices))
        self._surfaces[-1][2] += len(vertices)


    def _compact(self, x, y, z, face, start, length):
        # The surface mesh array will now end at this index.
        end = self._surfaces[-1][2] - 6

        if start == end:
            # The vertices being removed by this compaction are at the end of
            # the important part of the surface mesh array.  That means we can
            # just subtract from the important marker instead of copying fresh
            # data on top of these vertices.
            self._surfaces[-1][2] -= length
            return

        # Find the voxel that owns the vertices at the end of the surface mesh
        # array.
        mx, my, mz = self._surfaces[-1][1][end][:3]

        possibilities = [
            (mx - 1, my - 1, mz,     TOP),
            (mx,     my - 1, mz - 1, FRONT),
            (mx,     my,     mz - 1, BOTTOM),
            (mx,     my,     mz,     BACK),
            (mx,     my,     mz,     LEFT),
            (mx - 1, my,     mz - 1, RIGHT),
            ]
        # Use knowledge about the location of the first vertex of the first to
        # find the voxel which owns these vertices.
        for key in possibilities:
            if self._voxelToSurface.get(key) == (end, 6):
                break
        else:
            err(Exception(
                    "Could not find voxel owning vertices at end of surface "
                    "mesh array."))
            return


        # Change the tracking data for the voxel which used to be stored at the
        # end of the surface mesh.  Now it's stored wherever we're overwriting.
        self._voxelToSurface[key] = (start, length)
        # Actually overwrite.
        self._surfaces[-1][0][start:start + length] = self._surfaces[-1][1][
            end:self._surfaces[-1][2]]
        # Note that the surface mesh is shorter now.
        self._surfaces[-1][2] = end


    def _removeVoxel(self, x, y, z):
        for face in FACES:
            key = (x, y, z, face)
            if key in self._voxelToSurface:
                # Get rid of the vertices for this face of this voxel.
                begin, length = self._voxelToSurface.pop(key)
                self._compact(x, y, z, face, begin, length)
            else:
                # If the voxel is missing a face, that's because it has a
                # neighbor!  Append vertices for that neighbor's revealed face.
                # deltas to get to the neighbor of this face
                dx, dy, dz, rface = NEIGHBORS[face]

                # coordinates of the neighbor
                nx, ny, nz = x + dx, y + dy, z + dz

                # maximum coordinates of the voxel data
                mx, my, mz = self._terrain.voxels.shape

                # if the neighbor coordinates are out of bounds, we can't create
                # a face
                if (nx < 0 or ny < 0 or nz < 0 or
                    nx >= mx or ny >= my or nz >= mz):
                    continue

                # There may actually be no neighbor at all, if _removeVoxel is
                # only being called because we observed an EMPTY voxel for the
                # first time ever.
                terrainType = self._terrain.voxels[nx, ny, nz]
                if terrainType in (EMPTY, UNKNOWN):
                    continue

                # Otherwise we can!
                key = (nx, ny, nz, rface)
                if key not in self._voxelToSurface:
                    self._append(
                        key,
                        self._makeFace(
                            rface,
                            self._terrain.voxels[nx, ny, nz], nx, ny, nz))


    def _exposed(self, x, y, z, face):
        voxels = self._terrain.voxels
        mx, my, mz = voxels.shape

        dx, dy, dz, _ = NEIGHBORS[face]
        x += dx
        y += dy
        z += dz

        return (
            x < 0 or y < 0 or z < 0 or
            x >= mx or y >= my or z >= mz or
            voxels[x, y, z] in (EMPTY, UNKNOWN))


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
                else:
                    # If the neighbor is not empty, then one of *its* faces is
                    # now obscured, remove it.
                    dx, dy, dz, rface = NEIGHBORS[face]
                    nx, ny, nz = x + dx, y + dy, z + dz
                    try:
                        start, length = self._voxelToSurface.pop((
                                nx, ny, nz, rface))
                    except KeyError:
                        # Except the neighbor's is not in the surface mesh.
                        # This happens when a bunch of voxels appear at once,
                        # and we skipped adding the neighbor face because we saw
                        # this voxel (the one at x, y, z) and knew we'd just
                        # have to remove it.
                        pass
                    else:
                        self._compact(nx, ny, nz, rface, start, length)


    def changed(self, position, shape):
        """
        Examine the terrain type at every changed voxel and determine if there
        are any exposed faces.  If so, update the surface mesh array.
        """
        voxels = self._terrain.voxels

        # Visit each voxel in the changed region and re-determine if it should
        # now be part of the surface mesh.
        for x in range(int(position.x), int(position.x + shape.x)):
            for y in range(int(position.y), int(position.y + shape.y)):
                for z in range(int(position.z), int(position.z + shape.z)):

                    if voxels[x, y, z] == EMPTY:
                        self._removeVoxel(x, y, z)
                    elif voxels[x, y, z] != UNKNOWN:
                        self._addVoxel(x, y, z)
