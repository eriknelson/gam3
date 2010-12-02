
"""
Tests for L{game.terrain}.
"""

from numpy import array, concatenate

from twisted.trial.unittest import TestCase

from game.test.util import ArrayMixin
from game.vector import Vector
from game.terrain import (
    LEFT, RIGHT, TOP, BOTTOM, FRONT, BACK,
    EMPTY, GRASS, MOUNTAIN, DESERT, WATER,
    Terrain, SurfaceMesh, loadTerrainFromString,
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



class TerrainTests(TestCase):
    """
    Tests for L{terrain.Terrain}.
    """
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



class SurfaceMeshTests(TestCase, ArrayMixin):
    """
    Tests for L{terrain.SurfaceMesh}.
    """
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
        self.terrain = Terrain()
        self.surface = SurfaceMesh(self.terrain, self.texCoords, self.e)
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
            self.surface.surface[:self.surface.important],
            array([x, y, z, s, t], 'f') + array(
                list(_top + texture) + list(_front + texture) +
                list(_bottom + texture) +list(_back + texture) +
                list(_left + texture) + list(_right + texture),
                'f'))

        # Six vertices per face, six faces
        self.assertEquals(self.surface.important, 36)


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

        self.assertEquals(self.surface.important, 0)


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
            self.surface.surface[:self.surface.important],
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
        self.assertEquals(self.surface.important, 60)


    def test_removeSecondVoxel(self):
        """
        When a voxel changes from non-empty to empty and its vertices are not at
        the end of the surface mesh array, vertices from the end of the surface
        mesh array are used to overwrite the changed voxels vertices.
        """
        self.test_twoVoxels()
        x = self.x
        y = self.y
        z = self.z
        self.terrain.set(x, y, z, loadTerrainFromString("_"))
        s, t = self.texCoords[GRASS]

        texture = self.textureBase
        self.assertArraysEqual(
            self.surface.surface[:self.surface.important],
            array([x, y, z, s, t], 'f') + array(
                list(_top + texture) + list(_front + texture) +
                list(_bottom + texture) + list(_back + texture) +
                # Note the reversal of left and right here.  It had a right face
                # already, but its left face was buried by the adjacent mountain
                # and so had no vertices in the surface mesh.  Revealing the
                # left face causes vertices for the left face to be appended -
                # after the vertices for the right face, in this case.
                list(_right + texture) + list(_left + texture), 'f'))

        self.assertEquals(self.surface.important, 6)


    def test_existingTerrain(self):
        """
        When terrain already exists when L{SurfaceMesh} is constructed, the
        surface mesh for that terrain is computed immediately.
        """
        x, y, z = 3, 2, 1
        terrain = Terrain()
        terrain.set(x, y, z, loadTerrainFromString("M"))
        surface = SurfaceMesh(terrain, self.texCoords, self.e)
        s, t = self.texCoords[MOUNTAIN]

        texture = self.textureBase
        self.assertArraysEqual(
            surface.surface[:surface.important],
            array([x, y, z, s, t], 'f') + array(
                list(_top + texture) + list(_front + texture) +
                list(_bottom + texture) + list(_back + texture) +
                list(_left + texture) + list(_right + texture), 'f'))

        # Six vertices per face, six faces
        self.assertEquals(surface.important, 36)
