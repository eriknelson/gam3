# -*- test-case-name: game.test.test_view -*-

"""
View code!
"""

from __future__ import division

from OpenGL.GL import (
    GL_PROJECTION, GL_MODELVIEW,
    glMatrixMode, glViewport,
    glLoadIdentity, glPushMatrix, glPopMatrix,
    glColor,
    glTranslate)
from OpenGL.GLU import (
    gluPerspective, gluNewQuadric, gluSphere)

import pygame.display, pygame.locals

from twisted.python.filepath import FilePath
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from epsilon.structlike import record

from game import __file__ as gameFile


class Color(record("red green blue")):
    """
    An RGB color.
    """



class Vertex(record("x y z")):
    """
    A coordinate in three dimensional space.
    """



class Sphere(record("center radius color")):
    """
    A renderer for a sphere.

    @ivar center: A L{Vertex} giving the center of this sphere.

    @ivar radius: A number giving the radius of this sphere.

    @ivar color: A L{Color} giving the color of this sphere.
    """
    def __init__(self, *args, **kwargs):
        super(Sphere, self).__init__(*args, **kwargs)
        self.quad = gluNewQuadric()


    def paint(self):
        glPushMatrix()
        glColor(self.color.red, self.color.green, self.color.blue)
        glTranslate(self.center.x, self.center.y, self.center.z)
        gluSphere(self.quad, self.radius, 25, 25)
        glPopMatrix()


def loadImage(path):
    """
    Load an image from the L{FilePath} into a L{pygame.Surface}.

    @type path: L{FilePath}

    @rtype: L{pygame.Surface}
    """
    return pygame.image.load(path.path)



class ViewMixin(object):
    """
    A mixin which allows subclasses to have a parent.

    @ivar parent: The L{Window} to draw to.
    """

    def setParent(self, parent):
        """
        Set the C{parent} attribute.

        Do not call this unless you are L{Window.add}.
        """
        self.parent = parent



class Scene(ViewMixin):
    """
    A collection of things to be rendered.

    @ivar _items: A C{list} of things which are part of this scene and which
        will be rendered when this scene is rendered.
    """
    def __init__(self):
        self._items = []


    def displayInitialized(self, display):
        pass


    def add(self, item):
        self._items.append(item)


    def paint(self):
        for item in self._items:
            item.paint()



class Viewport(object):
    """
    Represent the location and size of the view onto the world.

    This object serves primarily to convert between model and view coordinates.

    @ivar modelPosition: two-tuple of ints giving the model position which
    corresponds to the bottom left corner of the view.

    @ivar viewSize: two-tuple of ints giving the width and height of the view.
    """
    def __init__(self, modelPosition, viewSize):
        """
        Initialize the Viewport.

        @param modelPosition: Value for C{modelPosition} attribute.
        @param viewSize: Value for C{viewSize} attribute.
        """
        self.modelPosition = modelPosition
        self.viewSize = viewSize


    def modelToView(self, position):
        """
        Convert the given model coordinates into view coordinates.

        @param position: A two-tuple of ints giving a position in the model
        coordinate system.

        @return: A two-tuple of ints giving a position in the view coordinate
        system.
        """
        return (
            position[0] - self.modelPosition[0],
            self.viewSize[1] - (position[1] - self.modelPosition[1]))


    def initialize(self):
        """
        Set up the viewport.
        """
        x, y = self.viewSize
        glViewport(0, 0, x, y)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(60.0, x / y, 0.5, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()


class Window(object):
    """
    A top-level PyGame-based window. This acts as a container for
    other view objects.

#     @ivar environment: The L{game.environment.Environment} which is being
#         displayed.
    @ivar clock: Something providing
        L{twisted.internet.interfaces.IReactorTime}.
    @ivar views: List of current child views.
    @ivar screen: The L{pygame.Surface} which will be drawn to.
    @ivar _paintCall: C{None} or the L{IDelayedCall} provider for a pending
        C{paint} call.
    @ivar controller: The current controller.

    @ivar display: Something like L{pygame.display}.
    @ivar event: Something like L{pygame.event}.
    """
    screen = None

    def __init__(self,
                 environment,
                 clock=reactor,
                 display=pygame.display,
                 event=pygame.event):
        environment.addObserver(self)
        self.viewport = Viewport((0, 0), (320, 240))
        self.clock = clock
        self.display = display
        self.views = []
        self._paintCall = None
        self.controller = None
        self.event = event
        self.scene = Scene()


    def dirty(self):
        """
        Mark the view as out of date and schedule a re-paint.
        """
        if self._paintCall is None:
            self._paintCall = self.clock.callLater(0, self.paint)


    def add(self, view):
        """
        Associate the given view object with this window.
        """
        view.setParent(self)
        if self.screen is not None:
            view.displayInitialized(self.screen)
        self.views.append(view)
        self.dirty()


    def draw(self, image, position):
        """
        Render an image at a position.
        """
        x, y = self.viewport.modelToView(position)
        self.screen.blit(image, (x, y - image.get_size()[1]))


    def paint(self):
        """
        Call C{paint} on all views which have been directly added to
        this Window.
        """
        if self._paintCall is not None:
            if self._paintCall.active():
                self._paintCall.cancel()
            self._paintCall = None

        self.scene.paint()
        self.display.flip()


    def handleInput(self):
        """
        Handle currently available pygame input events.
        """
        for event in self.event.get():
            if event.type == pygame.locals.QUIT:
                self.stop()
            elif self.controller and event.type == pygame.KEYDOWN:
                self.controller.keyDown(event.key)
            elif self.controller and event.type == pygame.KEYUP:
                self.controller.keyUp(event.key)


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
        self.screen = self.display.set_mode(
            self.viewport.viewSize,
            pygame.locals.OPENGL)
        self.viewport.initialize()
        for view in self.views:
            view.displayInitialized(self.screen)

        self._renderCall = LoopingCall(self.paint)
        self._renderCall.start(0.01, now=False)
        self._inputCall = LoopingCall(self.handleInput)
        finishedDeferred = self._inputCall.start(0.04, now=False)
        finishedDeferred.addCallback(lambda ign: self._renderCall.stop())
        finishedDeferred.addCallback(lambda ign: self.display.quit())

        return finishedDeferred


    def stop(self):
        """
        Stop updating this window and handling events for it.
        """
        self._inputCall.stop()


    def playerCreated(self, player):
        """
        Create a L{PlayerView}.
        """
        self.add(PlayerView(player))


    def playerRemoved(self, player):
        """
        Remove a L{PlayerView}.
        """
        for view in self.views:
            if isinstance(view, PlayerView) and view.player is player:
                self.views.remove(view)
                return


class PlayerView(ViewMixin):
    """
    A view for a player.

    @ivar player: The L{game.player.Player} object.

    @ivar _image: The L{pygame.Surface} which will be drawn to the display.  An
        attempt is made to keep the color depth of this image the same as the
        color depth of the display.

    @ivar image: The L{pygame.Surface} image which corresponds to a player.
        This is the original image loaded from disk.
    """

    def __init__(self, player, loader=loadImage):
        """
        @param loader: A callable like L{loadImage}.
        """
        self.player = player
        # look up the image data based on model object (and whether it
        # is friday the 13th)
        self._image = self.image = loader(
            FilePath(__file__).sibling("data").child("player.png"))


    def displayInitialized(self, surface):
        """
        Convert the loaded player image to the same depth as the given display
        surface, to help performance of all future paint operations.
        """
        bits = surface.get_bitsize()
        # XXX Only bother converting if we learned a number of bits.  This is a
        # hack to keep the unit tests happy, where sometimes an actual
        # pygame.Surface is loaded as self.image and the conversion then fails
        # because the display is not initialized (which corresponds to the times
        # when the surface does not know its color depth)
        if bits is not None:
            self._image = self.image.convert(bits)


    def paint(self):
        """
        Paint an image of the player at the player's current location.
        """
        self.parent.draw(self._image, self.player.getPosition())



class TerrainView(ViewMixin):
    """
    A view for terrain over a tract of land.

    @type terrain: L{dict}
    @ivar terrain: The terrain data, mapping positions to terrain types.

    @ivar loader: A callable like L{loadImage}.

    @ivar _depth: The color depth of the display surface or C{None} if it is not
        yet known.
    """
    _depth = None

    def __init__(self, terrain, loader):
        self.terrain = terrain
        self.loader = loader
        self._images = {}


    def displayInitialized(self, surface):
        """
        Capture the display surface color depth so that terrain images can be
        properly converted.

        Also discard the terrain image cache so all images returned in the
        future are converted to the correct depth.
        """
        self._depth = surface.get_bitsize()
        self._images.clear()


    def paint(self):
        """
        Paint all visible terrain to the L{Window}.
        """
        for position, terrainType in self.terrain.iteritems():
            self.parent.draw(self.getImageForTerrain(terrainType), position)


    def getImageForTerrain(self, terrainType):
        """
        @param terrainType: The terrain type.

        @rtype: L{Surface}
        @return: An image which represents the given C{terrainType}.
        """
        if terrainType not in self._images:
            image = self.loader(
                FilePath(gameFile).sibling('data').child(terrainType + '.png'))
            if self._depth is not None:
                image = image.convert(self._depth)
            self._images[terrainType] = image
        return self._images[terrainType]
