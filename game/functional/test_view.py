
from twisted.internet import reactor

from twisted.trial.unittest import TestCase

from game.environment import Environment
from game.direction import EAST
from game.player import Player

from game.view import Window
from game.view import PlayerView

class PlayerTests(TestCase):
    def setUp(self):
        self.environment = Environment(50, reactor.callLater)
        self.player = Player(
            (0, 0),
            movementVelocity=75,
            seconds=self.environment.seconds)

        # XXX PRIVATE VARIABLE USAGE ZOMG
        print getattr(self, self._testMethodName).__doc__


    def tearDown(self):
        if not raw_input("Did it work?").lower().startswith('y'):
            self.fail("User specified test failure")
        self.environment.stop() # clean up pending calls

    def test_tedium(self):
        """
        * A 320x240 window, black background, should be displayed.
        * Alt-f4 should close the window.
        """
        window = Window()
        return window.go()


    def test_initial_position(self):
        """
        The player image should be displayed at the top-left corner of the
        window.
        """
        window = Window(reactor.callLater)
        view = PlayerView(self.player)
        window.add(view)

        return window.go()


    def test_moves_around(self):
        """
        The player image should move from the top left of the screen to the top
        right of the screen.
        """
        window = Window(reactor.callLater)
        view = PlayerView(self.player)
        window.add(view)
        self.player.setDirection(EAST)
        return window.go()
