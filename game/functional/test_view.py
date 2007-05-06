
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
        The player image should be displayed at the top-left corner of the
        window.
        """
        player = Player((0, 0))

        window = Window(reactor.callLater)
        pview = PlayerView(player)
        window.add(pview)

        return window.go()


    def test_moves_around(self):
        """
        The player image should move back and forth between the top left and
        top right of the window.
        """
        player = Player((0, 0))
        window = Window(reactor.callLater)
        view = PlayerView(player)
        window.add(view)

        # XXX There should be a thing for translating model coordinates into
        # view coordinates and stuff.
        interval = 0.005
        def sched(what):
            call[0] = reactor.callLater(interval, what)

        def moveLeft():
            if player.position[0] >= 320 - view.image.get_size()[0]:
                sched(moveRight)
            else:
                player.move((1, 0))
                sched(moveLeft)

        def moveRight():
            if player.position[0] <= 0:
                sched(moveLeft)
            else:
                player.move((-1, 0))
                sched(moveRight)

        call = [reactor.callLater(0, moveLeft)]


        def stop(ignored):
            call[0].cancel()

        d = window.go()
        d.addCallback(stop)
        return d
