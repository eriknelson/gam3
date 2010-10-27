
from twisted.internet import reactor

from twisted.trial.unittest import TestCase

from game.environment import Environment
from game.direction import RIGHT
from game.player import Player

from game.controller import PlayerController

from game.view import Window, loadImage
from game.view import PlayerView, TerrainView
from game.terrain import GRASS


class FunctionalTestMixin:
    def setUp(self):
        # XXX PRIVATE VARIABLE USAGE ZOMG
        print getattr(self, self._testMethodName).__doc__


    def tearDown(self):
        if not raw_input("Did it work?").lower().startswith('y'):
            self.fail("User specified test failure")



class PlayerTests(FunctionalTestMixin, TestCase):
    def setUp(self):
        self.environment = Environment(50, reactor)
        self.environment.start()
        self.player = Player(
            (0, 0),
            speed=75,
            seconds=self.environment.seconds)

        FunctionalTestMixin.setUp(self)


    def tearDown(self):
        self.environment.stop() # clean up pending calls
        FunctionalTestMixin.tearDown(self)


    def test_tedium(self):
        """
        * A 320x240 window, black background, should be displayed.
        * Alt-f4 should close the window.
        """
        window = Window(self.environment)
        return window.go()


    def test_initial_position(self):
        """
        The player image should be displayed at the bottom-left corner of the
        window.
        """
        window = Window(self.environment)
        view = PlayerView(self.player)
        window.add(view)

        return window.go()


    def test_moves_around(self):
        """
        The player image should move from the bottom left of the screen to the
        bottom right of the screen.
        """
        window = Window(self.environment)
        view = PlayerView(self.player)
        window.add(view)
        self.player.setDirection(RIGHT)
        return window.go()


    def test_input_directs_player(self):
        """
        The arrow keys should direct the player in eight directions.
        """
        window = Window(self.environment)
        view = PlayerView(self.player)
        window.add(view)
        window.submitTo(PlayerController(self.player))
        return window.go()



class TerrainTests(FunctionalTestMixin, TestCase):
    """
    Tests for how terrain is rendered in the view.
    """
    def test_singleTile(self):
        """
        There should be a single square of grass terrain in the bottom left
        corner.
        """
        environment = Environment(50, reactor)
        window = Window(environment)
        view = TerrainView({(0, 0): GRASS}, loadImage)
        window.add(view)
        return window.go()
