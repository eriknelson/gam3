
from pygame import K_q, MOUSEBUTTONUP
from pygame.event import Event

from twisted.trial.unittest import TestCase
from twisted.internet import reactor

from game.functional.test_view3d import SceneMixin
from game.player import Player
from game.vector import Vector


class QuittableController(object):
    # XXX Make an interface for the controller and verify these fakes.
    def __init__(self, reactor, window):
        self.player = Player(Vector(0, 0, 0), 0, reactor.seconds)
        self.window = window


    def keyUp(self, key):
        if key == K_q:
            self.window.stop()


    def keyDown(self, key):
        pass


    def mouseMotion(self, pos, rel, buttons):
        pass



class StdoutReportingController(QuittableController):
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
    def _movementTest(self, grab):
        self.window.submitTo(StdoutReportingController(reactor, self.window))
        if grab:
            reactor.callLater(0, self.window._handleEvent, Event(MOUSEBUTTONUP))
        return self.window.go()


    def test_movement(self):
        """
        When the mouse is grabbed and moves, the direction of movement is
        written to stdout.
        """
        return self._movementTest(True)


    def test_noMovement(self):
        """
        When the mouse is not grabbed and moves, the movement is ignored (no
        output is produced).
        """
        return self._movementTest(False)


    def test_grab(self):
        """
        Clicking on the window grabs the mouse.  Clicking again releases it.
        """
        self.window.submitTo(QuittableController(reactor, self.window))
        return self.window.go()
