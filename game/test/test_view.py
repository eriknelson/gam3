"""
Unit tests for the basic functionality of view objects.

More thorough tests are in L{game.functional}.
"""

from twisted.trial.unittest import TestCase

from twisted.internet.task import Clock
from twisted.python.filepath import FilePath

import pygame
from pygame.event import Event

from game.view import Viewport, Window, PlayerView, loadImage
from game.player import Player
from game.test.util import PlayerCreationMixin
from game.controller import LEFT


class MockImage(object):
    """
    An object that is supposed to look like the thing returned by L{loadImage}.

    @ivar size: A two-tuple of ints giving the pixel dimensions of this image.
    """
    def __init__(self, size):
        self.size = size


    def get_size(self):
        """
        Return the size of this image.
        """
        return self.size



class MockSurface(object):
    """
    An object that is supposed to look like L{pygame.Surface}.

    @ivar blits: A list of two-tuples giving the arguments to all
    calls to the C{blit} method.

    @ivar fills: A list of three-tuples giving the colors passed to the C{fill}
    method.
    """
    def __init__(self):
        self.blits = []
        self.fills = []


    def blit(self, surface, position):
        """
        Record an attempt to blit another surface onto this one.
        """
        self.blits.append((surface, position))


    def fill(self, color):
        """
        Record an attempt to fill the entire surface with a particular color.
        """
        self.fills.append(color)



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



class MockView(object):
    """
    An object that is supposed to look like L{PersonView}.
    """
    parent = None
    painted = False

    def setParent(self, parent):
        """
        Set the C{parent} attribute.
        """
        self.parent = parent


    def paint(self):
        """
        Set the C{painted} attribute to True.
        """
        self.painted = True



class MockWindow(object):
    """
    An object that is supposed to look like L{Window}.

    @ivar draws: A list of two-tuples giving the arguments to all
    calls to the C{draw} method.

    @ivar dirtied: An integer giving the number of calls to the C{dirty}
    method.
    """
    def __init__(self):
        self.draws = []
        self.dirtied = 0


    def draw(self, image, position):
        """
        Record an attempt to render an image at a particular location.
        """
        self.draws.append((image, position))


    def dirty(self):
        """
        Record an attempt to dirty the window.
        """
        self.dirtied += 1



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
        self.display = MockDisplay()
        self.clock = Clock()
        self.event = MockEventSource()
        self.window = Window(scheduler=self.clock.callLater,
                             display=self.display,
                             event=self.event)
        self.surface = MockSurface()
        self.window.screen = self.surface


    def test_add(self):
        """
        Adding a view to a Window should set the window as the view's parent.
        """
        view = MockView()
        self.window.add(view)
        self.assertIdentical(view.parent, self.window)


    def test_dirty(self):
        """
        Dirtying a L{Window} should schedule a painting of the entire scene.
        """
        self.window.dirty()
        self.assertEqual(len(self.clock.calls), 1)
        call = self.clock.calls[0]
        self.assertEqual(call.getTime(), 0)
        self.assertEqual(call.func, self.window.paint)


    def test_duplicateDirty(self):
        """
        Dirtying a L{Window} again before the painting for a previous C{dirty}
        call has happened should not schedule a new call.
        """
        self.window.dirty()
        self.window.dirty()
        self.assertEqual(len(self.clock.calls), 1)
        call = self.clock.calls[0]
        self.assertEqual(call.getTime(), 0)
        self.assertEqual(call.func, self.window.paint)


    def test_dirtiedAgain(self):
        """
        Dirtying a L{Window} again after the painting for a previous C{dirty}
        call has happened should schedule a new call.
        """
        self.window.dirty()
        self.clock.advance(1)
        self.assertEqual(self.clock.calls, [])
        self.window.dirty()
        self.assertEqual(len(self.clock.calls), 1)
        call = self.clock.calls[0]
        self.assertEqual(call.getTime(), 1)
        self.assertEqual(call.func, self.window.paint)


    def test_addDirties(self):
        """
        Adding a child should schedule painting of the entire scene.
        """
        view = MockView()
        self.window.add(view)
        self.assertEqual(len(self.clock.calls), 1)
        call = self.clock.calls[0]
        self.assertEqual(call.getTime(), 0)
        self.assertEqual(call.func, self.window.paint)


    def test_explicitPaintCancelsDirtyPaint(self):
        """
        Calling L{Window.paint} explicitly before the painting for a previous
        C{dirty} call has happened should cancel the pending paint call.
        """
        self.window.dirty()
        self.window.paint()
        self.assertEqual(self.clock.calls, [])


    def test_paint(self):
        """
        Painting a window should paint all of its views.
        """
        view1 = MockView()
        view2 = MockView()
        self.window.add(view1)
        self.window.add(view2)
        self.window.paint()
        self.assertEqual(view1.painted, True)
        self.assertEqual(view2.painted, True)


    def test_paintFlipsAndClears(self):
        """
        Painting a window should flip the display and fill it with black.
        """
        self.window.paint()
        self.assertEqual(self.surface.fills, [(0, 0, 0)])
        self.assertEqual(self.display.flipped, 1)


    def test_draw(self):
        """
        Drawing an image at a location should blit it onto the screen
        at the correct position.
        """
        imageSize = (3, 8)
        drawPosition = (13, -1)
        viewSize = (32, 24)
        self.window.viewport.viewSize = viewSize
        self.window.screen = MockSurface()
        image = MockImage(imageSize)
        self.window.draw(image, drawPosition)
        self.assertEqual(
            self.window.screen.blits,
            [(image, (drawPosition[0],
                      viewSize[1] - drawPosition[1] - imageSize[1]))])


    def test_submitTo(self):
        """
        It should be possible to set the window's controller.
        """
        controller = object()
        self.window.submitTo(controller)
        self.assertEquals(self.window.controller, controller)


    def test_controllerGetsKeyDownEvents(self):
        """
        The controller should be called with key-down events.
        """
        controller = MockController()
        self.window.submitTo(controller)
        self.event.events = [Event(pygame.KEYDOWN, key=pygame.K_LEFT)]
        self.window.handleInput()
        self.assertEquals(controller.downs, [LEFT])


    def test_controllerGetsKeyUpEvents(self):
        """
        The controller should be called with key-up events.
        """
        controller = MockController()
        self.window.submitTo(controller)
        self.event.events = [Event(pygame.KEYUP, key=pygame.K_LEFT)]
        self.window.handleInput()
        self.assertEquals(controller.ups, [LEFT])


class MockEventSource(object):
    """
    An object that is supposed to look like L{pygame.event}.

    @ivar events: The events to return from L{get}.
    """

    def __init__(self):
        self.events = []

    def get(self):
        """Return the previously specified events.
        """
        return self.events


class MockController(object):
    """
    A controller which records events.

    @ivar downs: The recorded key-down events.
    @ivar ups: The recorded key-up events.
    """
    def __init__(self):
        self.downs = []
        self.ups = []

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


class PlayerViewTests(TestCase, PlayerCreationMixin):
    def setUp(self):
        self.player = self.makePlayer((3, 2))
        self.view = PlayerView(self.player)


    def test_initialization(self):
        """
        L{PlayerView} should take the player model as an argument to
        the initializer.
        """
        self.assertIdentical(self.view.player, self.player)


    def test_setParent(self):
        """
        Calling L{PlayerView.setParent} should set the C{parent}
        attribute of the player view.
        """
        self.view.setParent(2)
        self.assertEqual(self.view.parent, 2)


    def test_paint(self):
        """
        Calling L{PlayerView.paint} should draw an image object to the
        window.
        """
        window = MockWindow()
        self.view.setParent(window)
        self.view.paint()
        self.assertEqual(window.draws, [(self.view.image, (3, 2))])



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

