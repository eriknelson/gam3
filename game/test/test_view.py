"""
Unit tests for the basic functionality of view objects.

More thorough tests are in L{game.functional}.
"""

from twisted.trial.unittest import TestCase

from twisted.internet.task import Clock
from twisted.python.filepath import FilePath

from game.view import Window, PlayerView, loadImage
from game.player import Player


class MockSurface(object):
    """
    An object that is supposed to look like L{pygame.Surface}.

    @ivar blits: A list of two-tuples giving the arguments to all
    calls to the C{blit} method.
    """
    def __init__(self):
        self.blits = []


    def blit(self, surface, position):
        """
        Record an attempt to blit another surface onto this one.
        """
        self.blits.append((surface, position))



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
    """
    def __init__(self):
        self.draws = []


    def draw(self, image, position):
        """
        Record an attempt to render an image at a particular location.
        """
        self.draws.append((image, position))



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
        self.window = Window(scheduler=self.clock.callLater,
                             display=self.display)


    def test_add(self):
        """
        Adding a view to a Window should set the window as the view's parent.
        """
        view = MockView()
        self.window.add(view)
        self.assertIdentical(view.parent, self.window)


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


    def test_paintFlips(self):
        """
        Painting a window should flip the display.
        """
        self.window.paint()
        self.assertEqual(self.display.flipped, 1)


    def test_draw(self):
        """
        Drawing an image at a location should blit it onto the screen
        at the correct position.
        """
        self.window.screen = MockSurface()
        image = object()
        self.window.draw(image, (13, -1))
        self.assertEqual(self.window.screen.blits, [(image, (13, -1))])



class PlayerViewTests(TestCase):

    def test_initialization(self):
        """
        L{PlayerView} should take the player model as an argument to
        the initializer.
        """
        # XXX replace this with an object that has an addObserver method.
        o = object()
        pv = PlayerView(o)
        self.assertIdentical(pv.player, o)


    def test_setParent(self):
        """
        Calling L{PlayerView.setParent} should set the C{parent}
        attribute of the player view.
        """
        pv = PlayerView(None)
        pv.setParent(2)
        self.assertEqual(pv.parent, 2)


    def test_paint(self):
        """
        Calling L{PlayerView.paint} should draw an image object to the
        window.
        """
        player = Player((3, 2))
        window = MockWindow()
        playerView = PlayerView(player)
        playerView.setParent(window)
        playerView.paint()
        self.assertEqual(window.draws, [(playerView.image, (3, 2))])


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

