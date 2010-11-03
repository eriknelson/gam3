
from twisted.trial.unittest import TestCase
from twisted.internet import reactor

from game.vector import Vector
from game.environment import Environment
from game.view import (
    Window, StaticLight, Sphere, Color, TerrainView, loadImage)
from game.player import Player
from game.controller import PlayerController

from game.functional.util import FunctionalTestMixin


class SceneMixin(FunctionalTestMixin):
    # Keep things a bit away from the real origin, so we detect anything that
    # only accidentally works there.
    def origin(self, x, y, z):
        return Vector(5, 5, 5) + Vector(x, y, z)


    def setUp(self):
        self.environment = Environment(50, reactor)
        self.window = Window(self.environment)
        self.window.viewport.viewSize = (1024, 768)
        self.window.scene.addLight(StaticLight(self.origin(1, 1, -2)))
        self.window.scene.camera.position = self.origin(0, 0, 0)
        FunctionalTestMixin.setUp(self)



class ThreeDeeTests(SceneMixin, TestCase):
    """
    Tests for 3d capabilities of L{game.view}.
    """
    def test_sphere(self):
        """
        A red sphere should appear in the center of the window.
        """
        self.window.scene.add(
            Sphere(self.origin(0, 0, -3), 0.5, Color(1.0, 0.0, 0.0)))
        return self.window.go()


    def _cameraTranslationTest(self, axis):
        sphere = Sphere(self.origin(0, 0, -3), 0.5, Color(1.0, 0.0, 0.0))
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
        A red sphere should appear in the center of the window, then move
        smoothly to the left, then move smoothly back to the center.
        """
        return self._cameraTranslationTest('x')


    def test_cameraTranslationY(self):
        """
        A red sphere should appear in the center of the window, then move
        smoothly down, then move smoothly back to the center.
        """
        return self._cameraTranslationTest('y')


    def test_cameraTranslationZ(self):
        """
        A red sphere should appear in the center of the window, then move away
        (appearing to shrink), then move smoothly back to the center (growing
        back to its original size).
        """
        return self._cameraTranslationTest('z')


    def _cameraRotationTest(self, axis):
        sphere = Sphere(self.origin(0, 1, -3), 0.5, Color(1.0, 0.0, 0.0))
        self.window.scene.add(sphere)
        camera = self.window.scene.camera
        def rotate(amount):
            setattr(
                camera.orientation, axis,
                getattr(camera.orientation, axis) + amount)
        for i in range(200):
            reactor.callLater(1 + (i / 100.0), rotate, -0.2)
        for i in range(200):
            reactor.callLater(3 + (i / 100.0), rotate, 0.2)
        return self.window.go()


    def test_cameraRotationX(self):
        """
        A red sphere above the center of the window should smoothly as if you
        were turning your head upwards, then rotate back up to its starting
        position.
        """
        return self._cameraRotationTest('x')


    def test_cameraRotationY(self):
        """
        A red sphere above the center of the window should smoothly as if you
        were turning your head to the left, then rotate back to its starting
        position.
        """
        return self._cameraRotationTest('y')


    def test_cameraRotationZ(self):
        """
        A red sphere above the center of the window should smoothly rotate in
        the clockwise directions, then rotate back to its starting position.
        """
        return self._cameraRotationTest('z')


    def test_depth(self):
        """
        A red sphere is in front of a green sphere.
        """
        self.window.scene.add(
            Sphere(self.origin(0, 0, -2), 0.5, Color(1.0, 0.0, 0.0)))
        self.window.scene.add(
            Sphere(self.origin(0, 0.5, -5), 2.0, Color(0.0, 1.0, 0.0)))
        return self.window.go()



class TerrainViewTests(SceneMixin, TestCase):
    """
    Tests for rendering of stuff that makes up the ground.
    """

    # Keep things a bit away from the real origin, so we detect anything that
    # only accidentally works there.
    def origin(self, x, y, z):
        return Vector(5, 5, 5) + Vector(x, y, z)

    def setUp(self):
        SceneMixin.setUp(self)
        self.window.scene.camera.position = self.origin(0.5, 1, 0)
        self.terrain = {}
        self.view = TerrainView(self.terrain, loadImage)
        self.window.scene.add(self.view)


    def test_terrain(self):
        """
        A three by three arrangement of "terrain" should appear in the bottom
        part of the window in perspective.  The types of terrain from top to
        bottom, left to right, should be::

            yellow (desert), green (grass), grey (mountain)
            grey (mountain), yellow (desert), green (grass)
            green (grass), grey (mountain), yellow (desert)

        The terrain should appear to extend downwards rather than appearing two
        dimensional.
        """
        v = self.origin(0, 0, 0)
        self.terrain.update({
                (v.x - 1, v.y, v.z - 4): "grass",
                (v.x + 0, v.y, v.z - 4): "mountain",
                (v.x + 1, v.y, v.z - 4): "desert",

                (v.x - 1, v.y, v.z - 5): "mountain",
                (v.x + 0, v.y, v.z - 5): "desert",
                (v.x + 1, v.y, v.z - 5): "grass",

                (v.x - 1, v.y, v.z - 6): "desert",
                (v.x + 0, v.y, v.z - 6): "grass",
                (v.x + 1, v.y, v.z - 6): "mountain"})

        return self.window.go()


    def test_alone(self):
        """
        A single piece of green terrain should appear.
        """
        v = self.origin(0, 0, 0)
        self.terrain.update({(v.x, v.y, v.z - 5): "grass"})
        return self.window.go()


    def test_followCamera(self):
        """
        The left, right, up, and down arrow keys should allow the camera
        position to be moved left, right, forward, and backward.
        """
        player = Player(self.origin(0, 1, 0), 2.0, reactor.seconds)
        controller = PlayerController(player)
        self.window.submitTo(controller)
        v = self.origin(0, 0, 0)
        self.terrain.update({
                (v.x - 1, v.y, v.z - 4): "grass",
                (v.x + 0, v.y, v.z - 4): "mountain",
                (v.x + 1, v.y, v.z - 4): "desert",

                (v.x - 1, v.y, v.z - 5): "mountain",
                (v.x + 0, v.y, v.z - 5): "desert",
                (v.x + 1, v.y, v.z - 5): "grass",

                (v.x - 1, v.y, v.z - 6): "desert",
                (v.x + 0, v.y, v.z - 6): "grass",
                (v.x + 1, v.y, v.z - 6): "mountain"})
        return self.window.go()
