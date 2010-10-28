
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


    def _cameraTranslationTest(self, axis):
        sphere = Sphere(Vertex(0, 0, -3), 0.5, Color(1.0, 0.0, 0.0))
        self.window.scene.add(sphere)
        camera = self.window.scene.camera
        def move(amount):
            setattr(
                camera.position, axis, getattr(camera.position, axis) + amount)
        for i in range(100):
            reactor.callLater(1 + (i / 100.0), move, 0.01)
        for i in range(100):
            reactor.callLater(2 + (i / 100.0), move, -0.01)
        return self.window.go()


    def test_cameraTranslationX(self):
        """
        A red circle should appear in the center of the window, then move
        smoothly to the left, then move smoothly back to the center.
        """
        return self._cameraTranslationTest('x')


    def test_cameraTranslationY(self):
        """
        A red circle should appear in the center of the window, then move
        smoothly down, then move smoothly back to the center.
        """
        return self._cameraTranslationTest('y')


    def test_cameraTranslationZ(self):
        """
        A red circle should appear in the center of the window, then move away
        (appearing to shrink), then move smoothly back to the center (growing
        back to its original size).
        """
        return self._cameraTranslationTest('z')


    # def test_cameraRotationX(self):
    #     axis = 'x'
    #     sphere = Sphere(Vertex(0, 0, -3), 0.5, Color(1.0, 0.0, 0.0))
    #     self.window.scene.add(sphere)
    #     def move(amount):
    #         self.window.scene.camera
    #         setattr(sphere.center, axis, getattr(sphere.center, axis) + amount)
    #     for i in range(100):
    #         reactor.callLater(1 + (i / 100.0), move, -0.01)
    #     for i in range(100):
    #         reactor.callLater(2 + (i / 100.0), move, 0.01)
    #     return self.window.go()
