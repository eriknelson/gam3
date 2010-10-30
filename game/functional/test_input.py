
from twisted.trial.unittest import TestCase
from twisted.internet import reactor

from game.functional.test_view3d import SceneMixin
from game.player import Player
from game.vec3 import vec3

class StdoutReportingController(object):
    def __init__(self):
        self.player = Player(vec3(0, 0, 0), 0, reactor.seconds)


    def mouseMotion(self, pos, rel, buttons):
        """
        Report to standard out the direction of the mouse movement.
        """
        if rel[0] < 0:
            print 'left',
        elif rel[0] > 0:
            print 'right',
        if rel[1] < 0:
            print 'up',
        if rel[1] > 0:
            print 'down',
        print


class MouseInputTests(SceneMixin, TestCase):
    """
    Tests for mouse input.
    """
    def test_movement(self):
        """
        When the mouse moves, the direction of movement is written to stdout.
        """
        self.window.submitTo(StdoutReportingController())
        return self.window.go()
