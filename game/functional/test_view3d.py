
from twisted.trial.unittest import TestCase
from twisted.internet import reactor

from game.environment import Environment
from game.view import Viewport, Window, Sphere, Vertex, Color

from game.functional.util import FunctionalTestMixin


class ThreeDeeTests(FunctionalTestMixin, TestCase):
    """
    Tests for 3d capabilities of L{game.view}.
    """
    def setUp(self):
        self.viewport = Viewport(None, (640, 480))
        self.environment = Environment(50, reactor)
        self.window = Window(self.environment)
        FunctionalTestMixin.setUp(self)


    def test_sphere(self):
        """
        A red circle should appear in the center of the window.
        """
        self.window.scene.add(
            Sphere(Vertex(0, 0, -3), 0.5, Color(1.0, 0.0, 0.0)))
        return self.window.go()
