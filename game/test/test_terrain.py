
"""
Tests for L{game.terrain}.
"""

from numpy import array, concatenate

from twisted.trial.unittest import TestCase

from game.test.util import ArrayMixin
from game.vector import Vector
from game.terrain import (
    EMPTY, GRASS, MOUNTAIN, DESERT, WATER, Terrain, SurfaceMesh,
    loadTerrainFromString)


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
        self.e = 0.125
        self.texCoords = {
            MOUNTAIN: (0.5, 0.75),
            GRASS: (0.25, 0.5),
            }
        self.terrain = Terrain()
        self.surface = SurfaceMesh(self.terrain, self.texCoords, self.e)
        self.terrain.addObserver(self.surface.changed)


    def test_oneVoxel(self):
        """
        When there is no other terrain and one non-empty voxel is set, all six
        faces of it become visible.
        """
        e = self.e
        s, t = self.texCoords[MOUNTAIN]
        self.x = x = 1
        self.y = y = 2
        self.z = z = 3
        self.terrain.set(x, y, z, loadTerrainFromString("M"))

        # XXX Asserting one static pile of data equals another static pile of
        # data makes for a lousy unit test.  Assert something about results
        # instead. :/
        self.assertArraysEqual(
            self.surface.surface[:self.surface.important,:5],
            array([x, y, z, s, t], 'f') + array([
                    # Top face, triangle 1
                    [1, 1, 0, e, 0],
                    [0, 1, 0, 0, 0],
                    [0, 1, 1, 0, e],

                    # Top face, triangle 2
                    [1, 1, 0, e, 0],
                    [1, 1, 1, e, e],
                    [0, 1, 1, 0, e],

                    # Front face, triangle 1
                    [0, 1, 1, e, 0],
                    [0, 0, 1, 0, 0],
                    [1, 0, 1, 0, e],

                    # Front face, triangle 2
                    [0, 1, 1, e, 0],
                    [1, 1, 1, e, e],
                    [1, 0, 1, 0, e],

                    # Bottom face, triangle 1
                    [0, 0, 1, e, 0],
                    [0, 0, 0, 0, 0],
                    [1, 0, 0, 0, e],

                    # Bottom face, triangle 2
                    [0, 0, 1, e, 0],
                    [1, 0, 1, e, e],
                    [1, 0, 0, 0, e],

                    # Back face, triangle 1
                    [0, 0, 0, e, 0],
                    [0, 1, 0, 0, 0],
                    [1, 1, 0, 0, e],

                    [0, 0, 0, e, 0],
                    [1, 0, 0, e, e],
                    [1, 1, 0, 0, e],

                    # Left face, triangle 1
                    [0, 0, 0, e, 0],
                    [0, 0, 1, 0, 0],
                    [0, 1, 1, 0, e],

                    [0, 0, 0, e, 0],
                    [0, 1, 0, e, e],
                    [0, 1, 1, 0, e],

                    # Right face, triangle 1
                    [1, 0, 1, e, 0],
                    [1, 0, 0, 0, 0],
                    [1, 1, 0, 0, e],

                    [1, 0, 1, e, 0],
                    [1, 1, 1, e, e],
                    [1, 1, 0, 0, e],

                    ], 'f'))

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
        e = self.e
        ms, mt = self.texCoords[MOUNTAIN]
        gs, gt = self.texCoords[GRASS]

        self.x = x = 10
        self.y = y = 11
        self.z = z = 12
        self.terrain.set(x, y, z, loadTerrainFromString("MG"))

        self.assertArraysEqual(
            self.surface.surface[:self.surface.important,:5],
            concatenate((
                    # mountain
                    array([x, y, z, ms, mt], 'f') + array([
                            # Top face, triangle 1
                            [1, 1, 0, e, 0],
                            [0, 1, 0, 0, 0],
                            [0, 1, 1, 0, e],

                            # Top face, triangle 2
                            [1, 1, 0, e, 0],
                            [1, 1, 1, e, e],
                            [0, 1, 1, 0, e],

                            # Front face, triangle 1
                            [0, 1, 1, e, 0],
                            [0, 0, 1, 0, 0],
                            [1, 0, 1, 0, e],

                            # Front face, triangle 2
                            [0, 1, 1, e, 0],
                            [1, 1, 1, e, e],
                            [1, 0, 1, 0, e],

                            # Bottom face, triangle 1
                            [0, 0, 1, e, 0],
                            [0, 0, 0, 0, 0],
                            [1, 0, 0, 0, e],

                            # Bottom face, triangle 2
                            [0, 0, 1, e, 0],
                            [1, 0, 1, e, e],
                            [1, 0, 0, 0, e],

                            # Back face, triangle 1
                            [0, 0, 0, e, 0],
                            [0, 1, 0, 0, 0],
                            [1, 1, 0, 0, e],

                            [0, 0, 0, e, 0],
                            [1, 0, 0, e, e],
                            [1, 1, 0, 0, e],

                            # Left face, triangle 1
                            [0, 0, 0, e, 0],
                            [0, 0, 1, 0, 0],
                            [0, 1, 1, 0, e],

                            [0, 0, 0, e, 0],
                            [0, 1, 0, e, e],
                            [0, 1, 1, 0, e],
                            ], 'f'),
                    # grass
                    array([x + 1, y, z, gs, gt], 'f') + array([
                            # Top face, triangle 1
                            [1, 1, 0, e, 0],
                            [0, 1, 0, 0, 0],
                            [0, 1, 1, 0, e],

                            # Top face, triangle 2
                            [1, 1, 0, e, 0],
                            [1, 1, 1, e, e],
                            [0, 1, 1, 0, e],

                            # Front face, triangle 1
                            [0, 1, 1, e, 0],
                            [0, 0, 1, 0, 0],
                            [1, 0, 1, 0, e],

                            # Front face, triangle 2
                            [0, 1, 1, e, 0],
                            [1, 1, 1, e, e],
                            [1, 0, 1, 0, e],

                            # Bottom face, triangle 1
                            [0, 0, 1, e, 0],
                            [0, 0, 0, 0, 0],
                            [1, 0, 0, 0, e],

                            # Bottom face, triangle 2
                            [0, 0, 1, e, 0],
                            [1, 0, 1, e, e],
                            [1, 0, 0, 0, e],

                            # Back face, triangle 1
                            [0, 0, 0, e, 0],
                            [0, 1, 0, 0, 0],
                            [1, 1, 0, 0, e],

                            [0, 0, 0, e, 0],
                            [1, 0, 0, e, e],
                            [1, 1, 0, 0, e],

                            # Right face, triangle 1
                            [1, 0, 1, e, 0],
                            [1, 0, 0, 0, 0],
                            [1, 1, 0, 0, e],

                            [1, 0, 1, e, 0],
                            [1, 1, 1, e, e],
                            [1, 1, 0, 0, e],
                            ], 'f'))))

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
        e = self.e

        # XXX This only covers the top face.
        self.assertArraysEqual(
            self.surface.surface[:self.surface.important,:5],
            array([
                    # Top face, grass, triangle 1
                    [x + 2, y + 1, z + 0, s + e, t],
                    [x + 1, y + 1, z + 0, s + 0, t],
                    [x + 1, y + 1, z + 1, s + 0, t + e],

                    # Top face, grass, triangle 2
                    [x + 2, y + 1, z + 0, s + e, t],
                    [x + 2, y + 1, z + 1, s + e, t + e],
                    [x + 1, y + 1, z + 1, s + 0, t + e],
                    ], 'f'))

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
        e = self.e

        # XXX This only covers the top face.
        self.assertArraysEqual(
            surface.surface[:surface.important,:5],
            array([
                    # Top face, grass, triangle 1
                    [x + 1, y + 1, z + 0, s + e, t],
                    [x + 0, y + 1, z + 0, s + 0, t],
                    [x + 0, y + 1, z + 1, s + 0, t + e],

                    # Top face, grass, triangle 2
                    [x + 1, y + 1, z + 0, s + e, t],
                    [x + 1, y + 1, z + 1, s + e, t + e],
                    [x + 0, y + 1, z + 1, s + 0, t + e],
                    ], 'f'))

        self.assertEquals(surface.important, 6)
