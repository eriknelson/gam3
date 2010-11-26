"""
Unit tests for the basic functionality of view objects.

More thorough tests are in L{game.functional}.
"""

from twisted.trial.unittest import TestCase

from twisted.internet.task import Clock
from twisted.python.filepath import FilePath

import pygame
from pygame.event import Event

from game import __file__ as gameFile
from game.terrain import GRASS, MOUNTAIN, DESERT, WATER
from game.view import (
    Color, Scene,
    Viewport, Window, loadImage, TerrainView, PlayerView)
from game.test.util import MockSurface
from game.controller import K_LEFT
from game.environment import Environment
from game.player import Player
from game.vector import Vector


class MockDisplay(object):
    """
    An object that is supposed to look like L{pygame.display}.

    @ivar flipped: An integer giving the number of times C{flip} has
    been called.
    """
    flipped = 0

    def flip(self):
        """
        Record an attempt to swap the on-screen surface with the
        off-screen surface.
        """
        self.flipped += 1


    def set_mode(self, size, flags=0):
        """
        Create a display surface for the given mode.
        """
        self._screen = MockSurface("<display>", size)
        return self._screen


    def quit(self):
        """
        Ignored.  Should stop things, probably.
        """



class MockView(object):
    """
    An object that is supposed to look like L{PersonView}.
    """
    paints = 0

    def paint(self):
        """
        Set the C{painted} attribute to True.
        """
        self.paints += 1



class ViewportTests(TestCase):
    """
    Tests for L{Viewport}.
    """
    def test_modelToView(self):
        """
        L{Viewport.modelToView} should convert model coordinates to view
        coordinates based on the the model coordinates given to
        L{Viewport.__init__}.
        """
        view = Viewport((10, 20), (320, 240))
        self.assertEqual(
            view.modelToView((10, 20)),
            (0, 240))
        self.assertEqual(
            view.modelToView((10, 40)),
            (0, 220))
        self.assertEqual(
            view.modelToView((20, 40)),
            (10, 220))



class WindowTests(TestCase):
    """
    Tests for L{Window}.
    """
    def setUp(self):
        """
        Create a L{Window} with a mock scheduler and display.
        """
        self.granularity = 20
        self.clock = Clock()
        self.environment = Environment(self.granularity, self.clock.callLater)
        self.display = MockDisplay()
        self.event = MockEventSource()
        self.window = Window(environment=self.environment,
                             clock=self.clock,
                             display=self.display,
                             event=self.event)
        self.surface = MockSurface("<display>", (640, 480))
        self.window.screen = self.surface


    def test_defaultClock(self):
        """
        The L{Window}'s default clock should be L{twisted.internet.reactor}.
        """
        from twisted.internet import reactor
        window = Window(self.environment)
        self.assertIdentical(window.clock, reactor)


    def test_submitTo(self):
        """
        It should be possible to set the window's controller.
        """
        controller = MockController(self.clock)
        self.window.submitTo(controller)
        self.assertEquals(self.window.controller, controller)


    def test_controllerGetsKeyDownEvents(self):
        """
        The controller should be called with key-down events.
        """
        controller = MockController(self.clock)
        self.window.submitTo(controller)
        self.event.events = [Event(pygame.KEYDOWN, key=pygame.K_LEFT)]
        self.window.handleInput()
        self.assertEquals(controller.downs, [K_LEFT])


    def test_controllerGetsKeyUpEvents(self):
        """
        The controller should be called with key-up events.
        """
        controller = MockController(self.clock)
        self.window.submitTo(controller)
        self.event.events = [Event(pygame.KEYUP, key=pygame.K_LEFT)]
        self.window.handleInput()
        self.assertEquals(controller.ups, [K_LEFT])


    def test_playerCreated(self):
        """
        L{Window.playerCreated} adds a L{PlayerView} to the scene, wrapped
        around the created player.
        """
        # This calls playerCreated, since the Window adds itself as an observer.
        player = self.environment.createPlayer(Vector(1, 0, 2), 3)
        view = self.window.scene._items[-1]
        self.assertIsInstance(view, PlayerView)
        self.assertIdentical(view.player, player)


    def test_playerRemoved(self):
        """
        L{Window.playerRemoved} removes the L{PlayerView} for the L{Player}
        instanced passed to it.
        """
        player = self.environment.createPlayer(Vector(1, 0, 2), 3)
        self.environment.removePlayer(player)
        for view in self.window.scene._items:
            if isinstance(view, PlayerView) and view.player is player:
                self.fail("Found PlayerView for removed player")


    def test_go(self):
        """
        L{Window.go} initializes the display and returns a L{Deferred} which
        fires when the Window is closed.
        """
        d = self.window.go()
        L = []
        d.addBoth(L.append)
        self.assertEquals(L, [])
        self.window.stop()
        self.assertEquals(L, [None])
        self.assertEquals(
            self.display._screen.size, self.window.viewport.viewSize)




class MockEventSource(object):
    """
    An object that is supposed to look like L{pygame.event}.

    @ivar events: The events to return from L{get}.
    """

    def __init__(self):
        self.events = []


    def get(self):
        """
        Return the previously specified events.
        """
        return self.events



class MockController(object):
    """
    A controller which records events.

    @ivar downs: The recorded key-down events.
    @ivar ups: The recorded key-up events.
    """
    def __init__(self, clock):
        self.downs = []
        self.ups = []
        self.player = Player(Vector(0, 0, 0), 1, clock.seconds)


    def keyDown(self, key):
        """
        Record a key-down event.
        """
        self.downs.append(key)


    def keyUp(self, key):
        """
        Record a key-up event.
        """
        self.ups.append(key)



class ImageTests(TestCase):
    """
    Tests for image-related utility functionality.
    """
    def test_loadImage(self):
        """
        An image on the filesystem should be loadable into a pygame
        surface with L{loadImage}.
        """
        image = loadImage(FilePath(__file__).sibling('test-image.png'))
        self.assertEqual(image.get_size(), (16, 25))
        self.assertEqual(image.get_at((0, 0)), (0, 0, 0, 0))
        self.assertEqual(image.get_at((1, 0)), (255, 0, 0, 255))




class TerrainViewTests(TestCase):
    """
    Tests for L{game.terrain.TerrainView}.
    """
    def _imageForTerrainTest(self, type, result):
        paths = []
        def loadImage(path):
            paths.append(path)
            return MockSurface(path.basename(), (64, 64))
        view = TerrainView(None, loader=loadImage)
        image = view._getImageForTerrain(type)
        self.assertEquals(image.label, result)
        self.assertEqual(
            paths, [FilePath(gameFile).sibling('data').child(result)])


    def test_getImageForGrass(self):
        """
        L{TerrainView._getImageForTerrain} returns a surface holding a grassy
        image for the C{GRASS} terrain type.
        """
        self._imageForTerrainTest(GRASS, "grass.png")


    def test_getImageForMountain(self):
        """
        L{TerrainView._getImageForTerrain} returns a surface holding a rocky
        image for the C{MOUNTAIN} terrain type.
        """
        self._imageForTerrainTest(MOUNTAIN, "mountain.png")


    def test_getImageForDesert(self):
        """
        L{TerrainView._getImageForTerrain} returns a surface holding a sandy
        image for the C{DESERT} terrain type.
        """
        self._imageForTerrainTest(DESERT, "desert.png")


    def test_getImageForWater(self):
        """
        L{TerrainView._getImageForTerrain} returns a surface holding a watery
        image for the C{WATER} terrain type.
        """
        self._imageForTerrainTest(WATER, "water.png")



class ColorTests(TestCase):
    """
    Tests for L{Color}.
    """
    def test_attributes(self):
        """
        The three arguments passed to the L{Color} initializer are bound to its
        C{red}, C{green}, and C{blue} attributes.
        """
        c = Color(1, 2, 3)
        self.assertEquals(c.red, 1)
        self.assertEquals(c.green, 2)
        self.assertEquals(c.blue, 3)



class SceneTests(TestCase):
    """
    Tests for L{Scene}.
    """
    def test_paint(self):
        """
        L{Scene.paint} calls C{paint} on all objects previously added to it.
        """
        p = MockView()
        scene = Scene()
        scene.add(p)
        self.assertEquals(p.paints, 0)
        scene.paint()
        self.assertEquals(p.paints, 1)
        scene.paint()
        self.assertEquals(p.paints, 2)
