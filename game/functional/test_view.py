
from twisted.internet import reactor

from twisted.trial.unittest import TestCase

from game.player import Player

from game.view import Window
from game.view import PlayerView


class PlayerTests(TestCase):
    def setUp(self):
        # XXX PRIVATE VARIABLE USAGE ZOMG
        print getattr(self, self._testMethodName).__doc__

    def tearDown(self):
        if not raw_input("Did it work?").lower().startswith('y'):
            self.fail("User specified test failure")


    def test_tedium(self):
        """
        * A 320x240 window, black background, should be displayed.
        * Alt-f4 should close the window.
        """
        window = Window()
        return window.go()


    def test_initial_position(self):
        """
        The player should be displayed at the top-left corner of the window.
        """
        player = Player((0,0))

        window = Window(reactor.callLater)
        pview = PlayerView(player)
        window.add(pview)

        return window.go()

