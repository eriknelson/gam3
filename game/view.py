# -*- test-case-name: game.test.test_view -*-

"""
View code!
"""

from __future__ import division

from OpenGL.GL import (
    GL_PROJECTION, GL_MODELVIEW, GL_RGBA, GL_UNSIGNED_BYTE,
    GL_COLOR_MATERIAL, GL_LIGHTING, GL_DEPTH_TEST, GL_LIGHT0, GL_POSITION,
    GL_FRONT_AND_BACK, GL_EMISSION, GL_REPEAT, GL_LINEAR, GL_QUADS,
    GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT,
    glMatrixMode, glViewport,
    glGenTextures, glBindTexture, glTexParameteri, glTexImage2D, glTexCoord2d,
    glLoadIdentity, glPushMatrix, glPopMatrix,
    glEnable, glClear, glColor, glColorMaterial, glLight,
    glTranslate, glRotate, glBegin, glEnd, glVertex3f)
from OpenGL.GLU import (
    gluPerspective, gluNewQuadric, gluSphere)

import pygame.display, pygame.locals

from twisted.python.filepath import FilePath
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from epsilon.structlike import record

from game import __file__ as gameFile
from game.vec3 import vec3


def loadImage(path):
    """
    Load an image from the L{FilePath} into a L{pygame.Surface}.

    @type path: L{FilePath}

    @rtype: L{pygame.Surface}
    """
    return pygame.image.load(path.path)



class Color(record("red green blue")):
    """
    An RGB color.
    """



class Sphere(record("center radius color")):
    """
    A renderer for a sphere.

    @ivar center: A L{vec3} giving the center of this sphere.

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



class StaticCamera(record('position orientation')):
    """
    A fixed viewing perspective from which the scene will be observed.

    @ivar position: A L{vec3} giving the coordinates in the space of the
        perspective.

    @ivar orientation: A L{vec3} giving three rotations to orient the
        perspective.
    """
    def paint(self):
        glRotate(self.orientation.x, 1.0, 0.0, 0.0)
        glRotate(self.orientation.y, 0.0, 1.0, 0.0)
        glRotate(self.orientation.z, 0.0, 0.0, 1.0)
        glTranslate(-self.position.x, -self.position.y, -self.position.z)



class FollowCamera(record('player')):
    """
    A viewing perspective which is positioned wherever a particular player is
    positioned.

    @ivar player: The L{Player} this camera follows.
    """
    def paint(self):
        v = self.player.getPosition()
        o = self.player.orientation
        glRotate(o.x, 1.0, 0.0, 0.0)
        glRotate(o.y, 0.0, 1.0, 0.0)
        glRotate(o.z, 0.0, 0.0, 1.0)
        glTranslate(-v.x, -v.y, -v.z)



class StaticLight(record('position')):
    """
    A source of light in a scene.

    @ivar position: A L{vec3} giving the coordinates of the light source.
    """
    def paint(self):
        glEnable(GL_LIGHT0)
        glLight(
            GL_LIGHT0, GL_POSITION,
            (self.position.x, self.position.y, self.position.z))



class Scene(object):
    """
    A collection of things to be rendered.

    @ivar _items: A C{list} of things which are part of this scene and which
        will be rendered when this scene is rendered.

    @ivar _lights: A C{list} of light sources in the scene.
    """
    camera = None

    def __init__(self):
        self._items = []
        self._lights = []


    def add(self, item):
        self._items.append(item)


    def addLight(self, light):
        self._lights.append(light)


    def paint(self):
        """
        Display this scene.
        """
        # Clear what was rendered for the last frame, and discard the associated
        # culling geometry.
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Now the model matrix back into an unmodified state.
        glLoadIdentity()
        # Then set up the camera transformations.  These will affect everything
        # that follows, which is just what we want.
        if self.camera is not None:
            self.camera.paint()
        # Then illuminate stuff.
        for light in self._lights:
            light.paint()
        # Then put everything into the scene.
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

        # Hide things that are behind other things
        glEnable(GL_DEPTH_TEST)

        # Create the OpenGL viewport, setting the size of the window (in pixels)
        # and defining how the scene is projected onto it.
        glViewport(0, 0, x, y)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        # Field of view, aspect ratio, near clipping, far clipping
        gluPerspective(60.0, x / y, 0.5, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # This makes material color properties be defined by glColor calls,
        # necessary to get the right colors when lighting is enabled.
        glEnable(GL_COLOR_MATERIAL)
        # This might be desirable at some point, who knows.
        # glColorMaterial(GL_FRONT_AND_BACK, GL_EMISSION)

        # Make lighting work, because we like lights.
        glEnable(GL_LIGHTING)

        # Make textures work too.
        glEnable(GL_TEXTURE_2D)



class Window(object):
    """
    A top-level PyGame-based window. This acts as a container for
    other view objects.

#     @ivar environment: The L{game.environment.Environment} which is being
#         displayed.
    @ivar clock: Something providing
        L{twisted.internet.interfaces.IReactorTime}.
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
        self.controller = None
        self.event = event
        self.scene = Scene()
        self.scene.camera = StaticCamera(vec3(0, 0, 0), vec3(0, 0, 0))



    def paint(self):
        """
        Call C{paint} on all views which have been directly added to
        this Window.
        """
        self.scene.paint()
        self.display.flip()


    def handleInput(self):
        """
        Handle currently available pygame input events.
        """
        for event in self.event.get():
            if event.type == pygame.locals.QUIT or \
                    event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                self.stop()
            elif self.controller is not None:
                if event.type == pygame.KEYDOWN:
                    self.controller.keyDown(event.key)
                elif event.type == pygame.KEYUP:
                    self.controller.keyUp(event.key)
                elif event.type == pygame.MOUSEMOTION:
                    self.controller.mouseMotion(
                        event.pos, event.rel, event.buttons)


    def submitTo(self, controller):
        """
        Specify the given controller as the one to receive further
        events.
        """
        self.controller = controller
        # XXX Next line untested
        self.scene.camera = FollowCamera(controller.player)


    def go(self):
        """
        Show this window.

        @return: A Deferred that fires when this window is closed by the user.
        """
        pygame.init()
        pygame.event.set_grab(True)
        pygame.mouse.set_visible(False)
        self.screen = self.display.set_mode(
            self.viewport.viewSize,
            pygame.locals.DOUBLEBUF | pygame.locals.OPENGL)
        self.viewport.initialize()

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


    def playerRemoved(self, player):
        """
        Remove a L{PlayerView}.
        """



class TerrainView(object):
    """
    A view for terrain over a tract of land.

    @type terrain: L{dict}
    @ivar terrain: The terrain data, mapping positions to terrain types.

    @ivar loader: A callable like L{loadImage}.

    @ivar _images: A cache of L{pygame.Surface} instances, keyed on terrain
        types.  These images are the source for texture data for each type of
        terrain.

    @ivar _textures: A cache of texture identifiers, keyed on terrain types.
        The values are suitable for use with L{glBindTexture}.
    """
    square = [(0, 0), (1, 0), (1, 1), (0, 1)]

    directions = [
        # up
        ((0, 1, 0), [(0, 0, 0), (1, 0, 0), (1, 0, 1), (0, 0, 1)]),
        # down
        ((0, -1, 0), [(0, -1, 0), (1, -1, 0), (1, -1, 1), (0, -1, 1)]),
        # forward
        ((0, 0, -1), [(0, -1, 0), (1, -1, 0), (1, 0, 0), (0, 0, 0)]),
        # backward
        ((0, 0, 1), [(0, -1, 1), (1, -1, 1), (1, 0, 1), (0, 0, 1)]),
        # right
        ((-1, 0, 0), [(0, -1, 0), (0, 0, 0), (0, 0, 1), (0, -1, 1)]),
         # left
        ((1, 0, 0), [(1, -1, 0), (1, 0, 0), (1, 0, 1), (1, -1, 1)]),
        ]

    def __init__(self, terrain, loader):
        self.terrain = terrain
        self.loader = loader
        self._images = {}
        self._textures = {}


    def _getImageForTerrain(self, terrainType):
        """
        @param terrainType: The terrain type.

        @rtype: L{Surface}
        @return: An image which represents the given C{terrainType}.
        """
        if terrainType not in self._images:
            image = self.loader(
                FilePath(gameFile).sibling('data').child(terrainType + '.png'))
            self._images[terrainType] = image
        return self._images[terrainType]


    def _getTextureForTerrain(self, terrainType):
        """
        Return the texture which should be used to render a face of the given
        type of terrain.

        @param terrainType: A terrain identifier which can be passed to
            L{_getImageForTerrain}.
        """
        if terrainType not in self._textures:
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            image = self._getImageForTerrain(terrainType)
            raw = pygame.image.tostring(image, "RGBA", 0)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            width = image.get_width()
            height = image.get_height()
            glTexImage2D(
                GL_TEXTURE_2D, 0,
                GL_RGBA, width, height, 0,
                GL_RGBA,
                GL_UNSIGNED_BYTE,
                raw)
            self._textures[terrainType] = texture
        return self._textures[terrainType]


    def paint(self):
        """
        For all of the known terrain, render whatever faces are exposed.
        """
        for (x, y, z), terrainType in self.terrain.iteritems():
            for (dx, dy, dz), coordinates in self.directions:
                if (x + dx, y + dy, z + dz) in self.terrain:
                    continue

                # It is exposed, render a face.
                glBindTexture(
                    GL_TEXTURE_2D, self._getTextureForTerrain(terrainType))
                glBegin(GL_QUADS)
                for (tx, ty), (dx, dy, dz) in zip(self.square, coordinates):
                    glTexCoord2d(tx, ty)
                    glVertex3f(x + dx, y + dy, z + dz)
                glEnd()
