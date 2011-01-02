
"""
Tests for L{game.terrain}.
"""

from numpy import zeros, array, concatenate

from pygame import Surface

from twisted.trial.unittest import TestCase

from game.test.util import ArrayMixin
from game.vector import Vector
from game.terrain import (
    LEFT, RIGHT, TOP, BOTTOM, FRONT, BACK,
    UNKNOWN, EMPTY, GRASS, MOUNTAIN, DESERT, WATER,
    Terrain, SurfaceMesh, SurfaceMeshVertices, loadTerrainFromString,
    loadTerrainFromSurface,
    _top, _front, _bottom, _back, _left, _right)


class LoadTerrainFromStringTests(TestCase, ArrayMixin):
    """
    Tests for L{loadTerrainFromString}.
    """
    def test_loadEmpty(self):
        """
        L{loadTerrainFromString} interprets C{"_"} to mean empty space.
        """
        self.assertArraysEqual(
            loadTerrainFromString("_"),
            array([[[EMPTY]]], 'b'))


    def test_loadGrass(self):
        """
        L{loadTerrainFromString} interprets C{"G"} to mean grassy terrain.
        """
        self.assertArraysEqual(
            loadTerrainFromString("G"),
            array([[[GRASS]]], 'b'))


    def test_loadMountain(self):
        """
        L{loadTerrainFromString} interprets C{"M"} to mean mountainous terrain.
        """
        self.assertArraysEqual(
            loadTerrainFromString("M"),
            array([[[MOUNTAIN]]], 'b'))


    def test_loadDesert(self):
        """
        L{loadTerrainFromString} interprets C{"D"} to mean desert terrain.
        """
        self.assertArraysEqual(
            loadTerrainFromString("D"),
            array([[[DESERT]]], 'b'))


    def test_loadWater(self):
        """
        L{loadTerrainFromString} interprets C{"W"} to mean watery terrain.
        """
        self.assertArraysEqual(
            loadTerrainFromString("W"),
            array([[[WATER]]], 'b'))


    def test_varyingX(self):
        """
        L{loadTerrainFromString} assigns consecutive increasing integer X
        coordinates to consecutive characters on a line of input.
        """
        self.assertArraysEqual(
            loadTerrainFromString("GM"),
            array([[[GRASS]], [[MOUNTAIN]]], 'b'))


    def test_varyingY(self):
        """
        Groups of terrain lines separated by two consecutive newlines indicate
        data on different Y coordinates.  Consecutive groups are assigned
        consecutive decreasing integer Y coordinates.
        """
        self.assertArraysEqual(
            loadTerrainFromString("_G\n\nM_\n"),
            array([[[MOUNTAIN], [EMPTY]], [[EMPTY], [GRASS]]], 'b'))


    def test_varyingZ(self):
        """
        L{loadTerrainFromString} assigns consecutive increasing integer Z
        coordinates to characters from consecutive lines of input.
        """
        self.assertArraysEqual(
            loadTerrainFromString("G\nM"),
            array([[[GRASS, MOUNTAIN]]], 'b'))


    def test_ignoreTrailingWhitespace(self):
        """
        Trailing whitespace in the terrain file does not affect the resulting
        terrain data.
        """
        self.assertArraysEqual(
            loadTerrainFromString("GM\nMD\n\n"),
            array([[[GRASS, MOUNTAIN]], [[MOUNTAIN, DESERT]]], 'b'))



class TerrainTests(TestCase, ArrayMixin):
    """
    Tests for L{terrain.Terrain}.
    """
    def test_initial(self):
        """
        When L{Terrain} is instantiated, it allocates storage only for the voxel
        at (0, 0, 0) and indicates that the terrain type for that voxel is
        unknown.
        """
        terrain = Terrain()
        self.assertArraysEqual(terrain.voxels, array([[[UNKNOWN]]], 'b'))


    def test_dict(self):
        """
        L{Terrain.dict} returns a C{dict} containing all of the terrain data,
        with keys of three-tuples of voxel coordinates and values of terrain
        types.
        """
        terrain = Terrain()
        terrain.voxels = array([[[
                        GRASS, MOUNTAIN, EMPTY, WATER, UNKNOWN, DESERT]]], 'b')
        self.assertEquals(
            terrain.dict(),
            {(0, 0, 0): GRASS, (0, 0, 1): MOUNTAIN,
             (0, 0, 3): WATER, (0, 0, 5): DESERT})


    def test_observeChanges(self):
        """
        L{Terrain.observeChanges} takes a callable and causes later calls to
        L{Terrain.set} to call it with the position and extent of the changed
        terrain.
        """
        events = []
        terrain = Terrain()
        terrain.addObserver(
            lambda position, shape: events.append((position, shape)))
        terrain.set(4, 5, 6, loadTerrainFromString("GGG\nGGG"))
        self.assertEquals(events, [(Vector(4, 5, 6), Vector(3, 1, 2))])


    def test_unknownTerrain(self):
        """
        When there is a gap in known terrain left by L{Terrain.set} calls, the
        unknown terrain is initialized to L{UNKNOWN}.
        """
        terrain = Terrain()
        terrain.set(0, 0, 0, loadTerrainFromString("G"))
        terrain.set(0, 0, 2, loadTerrainFromString("G"))
        self.assertArraysEqual(
            terrain.voxels,
            array([[[GRASS, UNKNOWN, GRASS]]], 'b'))



class SurfaceMeshTests(TestCase, ArrayMixin):
    """
    Tests for L{terrain.SurfaceMesh}.
    """
    def surfaceFactory(self):
        """
        Give back a single pre-created array for the surface mesh to populate.
        The array is initialized in C{setUp}.
        """
        if self.surfaceArray is None:
            raise Exception(
                "Already gave out the only surface - "
                "these tests should only require one.")
        surfaceArray = self.surfaceArray
        self.surfaceArray = None
        return surfaceArray


    def setUp(self):
        e = self.e = 0.125

        # XXX This is currently the only texture arrangement, but it may come to
        # pass that something else is desired.  Each face may need its own
        # texture coordinates.
        self.textureBase = array([
                [0, 0, 0, e, 0],
                [0, 0, 0, 0, 0],
                [0, 0, 0, 0, e],
                [0, 0, 0, e, 0],
                [0, 0, 0, e, e],
                [0, 0, 0, 0, e]], 'f')
        self.texCoords = {
            MOUNTAIN: (0.5, 0.75),
            GRASS: (0.25, 0.5),
            }
        vertices = zeros((1000, 5), 'f')
        self.surfaceArray = self.mesh = SurfaceMeshVertices(
            vertices, vertices, 0)
        self.terrain = Terrain()
        self.surface = SurfaceMesh(
            self.terrain, self.surfaceFactory, self.texCoords, self.e)
        self.terrain.addObserver(self.surface.changed)


    def test_exposedLeft(self):
        """
        L{SurfaceMesh._exposed} checks the voxel in the negative direction along
        the X axis to determine if a left face is exposed or not.
        """
        self.terrain.set(0, 0, 0, loadTerrainFromString("_MMM"))
        self.assertTrue(self.surface._exposed(1, 0, 0, LEFT))
        self.assertFalse(self.surface._exposed(2, 0, 0, LEFT))


    def test_exposedRight(self):
        """
        L{SurfaceMesh._exposed} checks the voxel in the positive direction along
        the X axis to determine if a right face is exposed or not.
        """
        self.terrain.set(0, 0, 0, loadTerrainFromString("MMM_"))
        self.assertTrue(self.surface._exposed(2, 0, 0, RIGHT))
        self.assertFalse(self.surface._exposed(1, 0, 0, RIGHT))


    def test_exposedTop(self):
        """
        L{SurfaceMesh._exposed} checks the voxel in the positive direction along
        the Y axis to determine if a top face is exposed or not.
        """
        self.terrain.set(0, 0, 0, loadTerrainFromString("_\n\nM\n\nM\n\nM"))
        self.assertTrue(self.surface._exposed(0, 2, 0, TOP))
        self.assertFalse(self.surface._exposed(0, 1, 0, TOP))


    def test_exposedBottom(self):
        """
        L{SurfaceMesh._exposed} checks the voxel in the negative direction along
        the Y axis to determine if a bottom face is exposed or not.
        """
        self.terrain.set(0, 0, 0, loadTerrainFromString("M\n\nM\n\nM\n\n_"))
        self.assertTrue(self.surface._exposed(0, 1, 0, BOTTOM))
        self.assertFalse(self.surface._exposed(0, 2, 0, BOTTOM))


    def test_exposedFront(self):
        """
        L{SurfaceMesh._exposed} checks the voxel in the positive direction along
        the Z axis to determine if a front face is exposed or not.
        """
        self.terrain.set(0, 0, 0, loadTerrainFromString("M\nM\nM\n_"))
        self.assertTrue(self.surface._exposed(0, 0, 2, FRONT))
        self.assertFalse(self.surface._exposed(0, 0, 1, FRONT))


    def test_exposedBack(self):
        """
        L{SurfaceMesh._exposed} checks the voxel in the negative direction along
        the Z axis to determine if a back face is exposed or not.
        """
        self.terrain.set(0, 0, 0, loadTerrainFromString("_\nM\nM\nM"))
        self.assertTrue(self.surface._exposed(0, 0, 1, BACK))
        self.assertFalse(self.surface._exposed(0, 0, 2, BACK))


    def _compactTest(self, face, vertices):

        if face == BACK:
            other = FRONT
        else:
            other = BACK

        x, y, z = 3, 5, 7
        # Make something to overwrite.
        self.surface._append(
            (x, y, z, other), self.surface._makeFace(other, GRASS, x, y, z))

        # Put some front-face vertices at the end of the array.
        self.surface._append(
            (x, y, z, face), self.surface._makeFace(face, GRASS, x, y, z))

        # Overwrite that something from above.
        start, length = self.surface._voxelToSurface[x, y, z, other]
        self.surface._compact(x, y, z, other, start, length)

        # There should just be the front vertices left, in the place we told it
        # to overwrite.
        texture = self.textureBase
        s, t = self.texCoords[GRASS]
        self.assertArraysEqual(
            self.mesh.data[:self.mesh.important],
            array([x, y, z, s, t], 'f') + array(vertices + texture, 'f'))

        # And it should know where they are.
        self.assertEquals(
            self.surface._voxelToSurface[x, y, z, face], (start, length))


    def test_compactTop(self):
        """
        If the vertices at the end of the surface mesh array represent the top
        face of a voxel, they are identified as such by L{SurfaceMesh._compact},
        relocated, and the tracking dictionary updated to refer to their new
        location.
        """
        self._compactTest(TOP, _top)


    def test_compactFront(self):
        """
        If the vertices at the end of the surface mesh array represent the front
        face of a voxel, they are identified as such by L{SurfaceMesh._compact},
        relocated, and the tracking dictionary updated to refer to their new
        location.
        """
        self._compactTest(FRONT, _front)


    def test_compactBottom(self):
        """
        If the vertices at the end of the surface mesh array represent the
        bottom face of a voxel, they are identified as such by
        L{SurfaceMesh._compact}, relocated, and the tracking dictionary updated
        to refer to their new location.
        """
        self._compactTest(BOTTOM, _bottom)


    def test_compactBack(self):
        """
        If the vertices at the end of the surface mesh array represent the back
        face of a voxel, they are identified as such by L{SurfaceMesh._compact},
        relocated, and the tracking dictionary updated to refer to their new
        location.
        """
        self._compactTest(BACK, _back)


    def test_compactLeft(self):
        """
        If the vertices at the end of the surface mesh array represent the left
        face of a voxel, they are identified as such by L{SurfaceMesh._compact},
        relocated, and the tracking dictionary updated to refer to their new
        location.
        """
        self._compactTest(LEFT, _left)


    def test_compactRight(self):
        """
        If the vertices at the end of the surface mesh array represent the right
        face of a voxel, they are identified as such by L{SurfaceMesh._compact},
        relocated, and the tracking dictionary updated to refer to their new
        location.
        """
        self._compactTest(RIGHT, _right)


    def test_compactFailure(self):
        """
        If the vertices at the end of the surface mesh array cannot be
        associated with a face, an error is logged and the array is not changed.
        """
        # Stick some nice vertices in there
        first = self.surface._makeFace(FRONT, GRASS, 1, 2, 3)
        self.surface._append((1, 2, 3, FRONT), first)

        second = self.surface._makeFace(BACK, GRASS, 3, 2, 1)
        # Mangle it so it won't be recognized - this is probably a simulation of
        # a bug somewhere in the terrain module.
        second[0] = [10, 11, 12, 13, 14]
        self.surface._append((3, 2, 1, BACK), second)

        self.surface._compact(1, 2, 3, FRONT, 0, 6)
        self.assertEquals(len(self.flushLoggedErrors()), 1)
        self.assertArraysEqual(self.mesh.data[:6], first)
        self.assertArraysEqual(self.mesh.data[6:12], second)
        self.assertEquals(self.mesh.important, 12)


    def test_oneVoxel(self):
        """
        When there is no other terrain and one non-empty voxel is set, all six
        faces of it become visible.
        """
        s, t = self.texCoords[MOUNTAIN]
        self.x = x = 1
        self.y = y = 2
        self.z = z = 3
        self.terrain.set(x, y, z, loadTerrainFromString("M"))

        texture = self.textureBase
        self.assertArraysEqual(
            self.mesh.data[:self.mesh.important],
            array([x, y, z, s, t], 'f') + array(
                list(_top + texture) + list(_front + texture) +
                list(_bottom + texture) +list(_back + texture) +
                list(_left + texture) + list(_right + texture),
                'f'))

        # Six vertices per face, six faces
        self.assertEquals(self.mesh.important, 36)


    def test_unchangedVoxel(self):
        """
        When a previously non-empty voxel is part of a changed prism but remains
        non-empty, no new vertices are added to the surface mesh array for it.
        """
        self.test_oneVoxel()
        self.test_oneVoxel()


    def test_removeSingleVoxel(self):
        """
        When a previously non-empty voxel becomes empty, its vertexes are
        removed from the surface mesh array.
        """
        self.test_oneVoxel()
        self.terrain.set(self.x, self.y, self.z, loadTerrainFromString("_"))

        self.assertEquals(self.mesh.important, 0)


    def test_twoVoxels(self):
        """
        When there is no other terrain and two non-empty adjacent voxels are
        set, all faces except the touching faces become visible.
        """
        ms, mt = self.texCoords[MOUNTAIN]
        gs, gt = self.texCoords[GRASS]

        self.x = x = 10
        self.y = y = 11
        self.z = z = 12
        self.terrain.set(x, y, z, loadTerrainFromString("MG"))

        texture = self.textureBase
        self.assertArraysEqual(
            self.mesh.data[:self.mesh.important],
            concatenate((
                    # mountain
                    array([x, y, z, ms, mt], 'f') + array(
                        list(_top + texture) + list(_front + texture) +
                        list(_bottom + texture) + list(_back + texture) +
                        list(_left + texture), 'f'),
                    # grass
                    array([x + 1, y, z, gs, gt], 'f') + array(
                        list(_top + texture) + list(_front + texture) +
                        list(_bottom + texture) + list(_back + texture) +
                        list(_right + texture), 'f'))))
        # Six vertices per face, ten faces
        self.assertEquals(self.mesh.important, 60)


    def test_removeSecondVoxel(self):
        """
        When a voxel changes from non-empty to empty and its vertices are not at
        the end of the surface mesh array, vertices from the end of the surface
        mesh array are used to overwrite the changed voxels vertices.
        """
        x, y, z = 2, 4, 6

        self.terrain.set(x, y, z, loadTerrainFromString("M_G"))

        self.terrain.set(x, y, z, loadTerrainFromString("_"))
        s, t = self.texCoords[GRASS]
        offset = array([x + 2, y, z, s, t], 'f') + self.textureBase
        self.assertVertices(
            self.mesh.data,
            [(RIGHT, _right + offset),
             (LEFT, _left + offset),
             (BACK, _back + offset),
             (BOTTOM, _bottom + offset),
             (FRONT, _front + offset),
             (TOP, _top + offset)],
            36)


    def test_existingTerrain(self):
        """
        When terrain already exists when L{SurfaceMesh} is constructed, the
        surface mesh for that terrain is computed immediately.
        """
        x, y, z = 3, 2, 1
        terrain = Terrain()
        terrain.set(x, y, z, loadTerrainFromString("M"))
        self.surfaceArray = self.mesh
        SurfaceMesh(
            terrain, self.surfaceFactory, self.texCoords, self.e)
        s, t = self.texCoords[MOUNTAIN]

        offset = array([x, y, z, s, t], 'f') + self.textureBase
        self.assertVertices(
            self.mesh.data,
            [(TOP, _top + offset),
             (FRONT, _front + offset),
             (BOTTOM, _bottom + offset),
             (BACK, _back + offset),
             (LEFT, _left + offset),
             (RIGHT, _right + offset)],
            36)


    def assertVertices(self, surface, expected, total):
        pieces = []
        for i in range(0, total, 6):
            pieces.append(surface[i:i + 6])

        notFound = []
        for (face, vertices) in expected:
            for n, piece in enumerate(pieces):
                if (vertices == piece).all():
                    del pieces[n]
                    break
            else:
                notFound.append((face, vertices))

        if notFound:
            self.fail(
                "Some expected vertices not found in surface mesh:\n"
                "    notFound = %r\n"
                "    pieces = %r\n" % (notFound, pieces))
        if pieces:
            self.fail(
                "Some extra vertices left over:\n"
                "    notFound = %r\n"
                "    pieces = %r\n" % (notFound, pieces))


    def test_revealedFace(self):
        """
        When a voxel becomes empty and was adjacent to another voxel, the
        vertices for the revealed face of the remaining voxel is added to the
        surface mesh array.
        """
        x, y, z = 1, 3, 5
        self.terrain.set(x, y, z, loadTerrainFromString("GM"))
        self.terrain.set(x, y, z, loadTerrainFromString("_"))

        s, t = self.texCoords[MOUNTAIN]
        offset = array([x + 1, y, z, s, t], 'f') + self.textureBase
        self.assertVertices(
            self.mesh.data,
            [(TOP, _top + offset),
             (FRONT, _front + offset),
             (BOTTOM, _bottom + offset),
             (BACK, _back + offset),
             (LEFT, _left + offset),
             (RIGHT, _right + offset)],
            36)


    def test_obscuredFace(self):
        """
        When a voxel becomes non-empty and is adjacent to another non-empty
        voxel, the vertices for the obscured face of the original voxel are
        removed from the surface mesh array.
        """
        x, y, z = 1, 3, 5
        self.terrain.set(x, y, z, loadTerrainFromString("_M"))
        self.terrain.set(x, y, z, loadTerrainFromString("G"))

        gs, gt = self.texCoords[GRASS]
        ms, mt = self.texCoords[MOUNTAIN]
        goffset = array([x, y, z, gs, gt], 'f') + self.textureBase
        moffset = array([x + 1, y, z, ms, mt], 'f') + self.textureBase
        self.assertVertices(
            self.mesh.data,
            [(TOP, _top + goffset),
             (FRONT, _front + goffset),
             (BOTTOM, _bottom + goffset),
             (BACK, _back + goffset),
             (LEFT, _left + goffset),

             (TOP, _top + moffset),
             (FRONT, _front + moffset),
             (BOTTOM, _bottom + moffset),
             (BACK, _back + moffset),
             (RIGHT, _right + moffset)],
            60)



class LoadTerrainFromSurfaceTests(TestCase):
    """
    Tests for L{loadTerrainFromSurface}.
    """
    def test_loadEmpty(self):
        """
        If an empty surface is passed to L{loadTerrainFromSurface}, a L{Terrain}
        with no data is returned.
        """
        terrain = loadTerrainFromSurface(Surface((0, 0)))
        self.assertIsInstance(terrain, Terrain)
        self.assertEquals(terrain.dict(), {})


    def test_height(self):
        """
        L{loadTerrainFromSurface} uses the red color component to determine how
        many voxels to stack.
        """
        surface = Surface((1, 1))
        surface.set_at((0, 0), (3, 0, 0))
        terrain = loadTerrainFromSurface(surface)
        self.assertEquals(
            terrain.dict(),
            {(0, 0, 0): MOUNTAIN,
             (0, 1, 0): MOUNTAIN,
             (0, 2, 0): GRASS})


    def test_varyingX(self):
        """
        L{loadTerrainFromSurface} varies the x coordinate of the loaded terrain
        with the x coordinate of the image data.
        """
        surface = Surface((2, 1))
        surface.set_at((0, 0), (3, 0, 0))
        surface.set_at((1, 0), (2, 0, 0))
        terrain = loadTerrainFromSurface(surface)
        self.assertEquals(
            terrain.dict(),
            {(0, 0, 0): MOUNTAIN, (1, 0, 0): MOUNTAIN,
             (0, 1, 0): MOUNTAIN, (1, 1, 0): GRASS,
             (0, 2, 0): GRASS})


    def test_varyingZ(self):
        """
        L{loadTerrainFromSurface} varies the z coordinate of the loaded terrain
        with the y coordinate of the image data.
        """
        surface = Surface((1, 2))
        surface.set_at((0, 0), (3, 0, 0))
        surface.set_at((0, 1), (2, 0, 0))
        terrain = loadTerrainFromSurface(surface)
        self.assertEquals(
            terrain.dict(),
            {(0, 0, 0): MOUNTAIN, (0, 0, 1): MOUNTAIN,
             (0, 1, 0): MOUNTAIN, (0, 1, 1): GRASS,
             (0, 2, 0): GRASS})
