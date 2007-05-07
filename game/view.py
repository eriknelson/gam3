# -*- test-case-name: game.test.test_view -*-

"""
View code!
"""

import pygame.display, pygame.locals

from twisted.python.filepath import FilePath
from twisted.internet.task import LoopingCall


def loadImage(path):
    """
    Load an image from the L{FilePath} into a L{pygame.Surface}.

    @type path: L{FilePath}

    @rtype: L{pygame.Surface}
    """
    return pygame.image.load(path.path)



class Window(object):
    """
    A top-level PyGame-based window. This acts as a container for
    other view objects.

    @ivar schedule: Something like
        L{twisted.internet.interfaces.IReactorTime.callLater}.
    @ivar views: List of current child views.
    @ivar screen: The L{pygame.Surface} which will be drawn to.
    @ivar _paintCall: C{None} or the L{IDelayedCall} provider for a pending
        C{paint} call.
    @ivar controller: The current controller.

    @ivar display: Something like L{pygame.display}.
    @ivar event: Something like L{pygame.event}.
    """

    def __init__(self, scheduler=lambda x, y: None,
                 display=pygame.display,
                 event=pygame.event):
        self.schedule = scheduler
        self.display = display
        self.views = []
        self._paintCall = None
        self.controller = None
        self.event = event


    def dirty(self):
        """
        Mark the view as out of date and schedule a re-paint.
        """
        if self._paintCall is None:
            self._paintCall = self.schedule(0, self.paint)


    def add(self, view):
        """
        Associate the given view object with this window.
        """
        view.setParent(self)
        self.views.append(view)
        self.dirty()


    def draw(self, image, position):
        """
        Render an image at a position.
        """
        self.screen.blit(image, position)


    def paint(self):
        """
        Call C{paint} on all views which have been directly added to
        this Window.
        """
        if self._paintCall is not None:
            if self._paintCall.active():
                self._paintCall.cancel()
            self._paintCall = None
        self.screen.fill((0, 0, 0))
        for view in self.views:
            view.paint()
        self.display.flip()


    def handleInput(self):
        """
        Handle currently available pygame input events.
        """
        for event in self.event.get():
            if event.type == pygame.locals.QUIT:
                self._inputCall.stop()
            elif self.controller and event.type == pygame.KEYDOWN:
                self.controller.keyDown(event.key)


    def submitTo(self, controller):
        """
        Specify the given controller as the one to receive further
        events.
        """
        self.controller = controller


    def go(self):
        """
        Show this window.

        @return: A Deferred that fires when this window is closed by the user.
        """
        pygame.init()
        self.screen = self.display.set_mode((320, 240),
                                            pygame.locals.DOUBLEBUF)

        self._renderCall = LoopingCall(self.paint)
        self._renderCall.start(0.01)
        self._inputCall = LoopingCall(self.handleInput)
        finishedDeferred = self._inputCall.start(0.04)
        finishedDeferred.addCallback(lambda ign: self._renderCall.stop())
        finishedDeferred.addCallback(lambda ign: self.display.quit())

        return finishedDeferred



class PlayerView(object):
    """
    A view for a player.

    @ivar player: The L{game.player.Player} object.

    @ivar parent: The L{Window} to draw to.
    """

    def __init__(self, player):
        self.player = player
        # look up the image data based on model object (and whether it
        # is friday the 13th)
        self.image = loadImage(
            FilePath(__file__).sibling("data").child("player.png"))


    def setParent(self, parent):
        """
        Set the C{parent} attribute.

        Do not call this unless you are L{Window.add}.
        """
        self.parent = parent


    def paint(self):
        """
        Paint an image of the player at the player's current location.
        """
        self.parent.draw(self.image, self.player.getPosition())


