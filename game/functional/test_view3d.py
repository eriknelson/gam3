
from twisted.trial.unittest import TestCase
from twisted.internet import reactor

from game.vector import Vector
from game.environment import Environment
from game.terrain import loadTerrainFromString
from game.view import (
    Window, StaticLight, Sphere, Color, PlayerView)
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
        self.terrain = self.environment.terrain
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
        A red sphere above the center of the window should smoothly rotate as if
        you were turning your head upwards, then rotate back up to its starting
        position.
        """
        return self._cameraRotationTest('x')


    def test_cameraRotationY(self):
        """
        A red sphere above the center of the window should smoothly rotate as if
        you were turning your head to the left, then rotate back to its starting
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

    def setUp(self):
        SceneMixin.setUp(self)
        self.window.scene.camera.position = Vector(-0.5, 1.1, 5)
        self.view = self.window.scene._items[0]


    def test_alone(self):
        """
        A single piece of green terrain should appear.
        """
        self.terrain.set(0, 0, 0, loadTerrainFromString("G"))
        return self.window.go()


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
        self.terrain.set(0, 0, 0, loadTerrainFromString(
                "GMD\n"
                "MDG\n"
                "DGM\n"))
        return self.window.go()


    def test_empty(self):
        """
        A grass voxel and a mountain voxel should be rendered separated by an
        empty voxel.
        """
        self.terrain.set(0, 0, 0, loadTerrainFromString("G_M"))
        return self.window.go()


    def test_followCamera(self):
        """
        The WASD (as well as up, left, right, and down arrow) keys should allow
        the camera position to be moved left, right, forward, and backward.
        """
        player = Player(self.origin(0, 1, 0), 2.0, reactor.seconds)
        controller = PlayerController(player)
        self.window.submitTo(controller)
        self.terrain.set(0, 0, 0, loadTerrainFromString(
                "GMD\n"
                "MDG\n"
                "DGM\n"))
        return self.window.go()


    def test_dynamicUpdate(self):
        """
        One green cube should appear, then a grey cube to its left, then the
        green cube should disappear.
        """
        self.window.scene.camera.position = Vector(2, 1.1, 5)

        reactor.callLater(
            1.0, self.terrain.set, 1, 0, 0, loadTerrainFromString("G"))

        reactor.callLater(
            2.0, self.terrain.set, 0, 0, 0, loadTerrainFromString("M"))

        reactor.callLater(
            3.0, self.terrain.set, 1, 0, 0, loadTerrainFromString("_"))

        return self.window.go()



class PlayerViewTests(SceneMixin, TestCase):
    """
    Tests for L{PlayerView}.
    """
    def test_rotation(self):
        """
        A depiction of another player (an upsidedown pyramid) should appear in
        the center of the screen, spinning.
        """
        player = Player(self.origin(0, 0, -3), 2.0, reactor.seconds)
        self.window.scene.add(PlayerView(player))
        def turn():
            player.turn(0, 1)
            c[0] = reactor.callLater(0.01, turn)
        c = [reactor.callLater(0.01, turn)]
        d = self.window.go()
        def finish(passthrough):
            c[0].cancel()
            return passthrough
        d.addBoth(finish)
        return d
