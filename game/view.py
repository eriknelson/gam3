# -*- test-case-name: game.test.test_view -*-

"""
View code!
"""

from __future__ import division

from numpy import zeros

from OpenGL.GL import (
    GL_PROJECTION, GL_MODELVIEW, GL_RGBA, GL_UNSIGNED_BYTE,
    GL_COLOR_MATERIAL, GL_LIGHTING, GL_DEPTH_TEST, GL_LIGHT0, GL_POSITION,
    GL_REPEAT, GL_TRIANGLES,
    GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_TEXTURE_WRAP_T, GL_TEXTURE_MAG_FILTER,
    GL_TEXTURE_MIN_FILTER, GL_COLOR_BUFFER_BIT, GL_DEPTH_BUFFER_BIT, GL_NEAREST,
    GL_TEXTURE_COORD_ARRAY,
    glMatrixMode, glViewport,
    glGenTextures, glBindTexture, glTexParameteri, glTexImage2D,
    glLoadIdentity, glPushMatrix, glPopMatrix,
    glEnable, glClear, glColor, glLight,
    glTranslate, glRotate, glBegin, glEnd, glVertex3f,
    glEnableClientState, glDisableClientState, glVertexPointer, glDrawArrays,
    GL_FLOAT, GL_VERTEX_ARRAY, glTexCoordPointer)
from OpenGL.GLU import (
    gluPerspective, gluNewQuadric, gluSphere)
from OpenGL.arrays.vbo import VBO

import pygame.display, pygame.locals

from twisted.python.filepath import FilePath
from twisted.internet.task import LoopingCall
from twisted.internet import reactor

from epsilon.structlike import record

from game import __file__ as gameFile
from game.vector import Vector
from game.terrain import (
    UNKNOWN, GRASS, MOUNTAIN, DESERT, WATER, CHUNK_GRANULARITY,
    SurfaceMesh, SurfaceMeshVertices)
from game.network import GetTerrain


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



def quantize(quantization, value):
    """
    Return the nearest integer smaller than C{value} which is a multiple of
    C{quantization}.

    @type quantization: C{int}
    @type value: C{int}
    @rtype: C{int}
    """
    return value - value % quantization



class Sphere(record("center radius color")):
    """
    A renderer for a sphere.

    @ivar center: A L{Vector} giving the center of this sphere.

    @ivar radius: A number giving the radius of this sphere.

    @ivar color: A L{Color} giving the color of this sphere.
    """
    quad = None
    def paint(self):
        if self.quad is None:
            self.quad = gluNewQuadric()

        glPushMatrix()
        glColor(self.color.red, self.color.green, self.color.blue)
        glTranslate(self.center.x, self.center.y, self.center.z)
        gluSphere(self.quad, self.radius, 25, 25)
        glPopMatrix()



class StaticCamera(record('position orientation')):
    """
    A fixed viewing perspective from which the scene will be observed.

    @ivar position: A L{Vector} giving the coordinates in the space of the
        perspective.

    @ivar orientation: A L{Vector} giving three rotations to orient the
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
        # XXX Put the camera somewhere in the middle-ish of the player model.
        # This is a wild guess for now, camera position data should be available
        # from the model at some later point.
        glTranslate(-v.x - 0.5, -v.y - 2, -v.z - 0.5)



class StaticLight(record('position')):
    """
    A source of light in a scene.

    @ivar position: A L{Vector} giving the coordinates of the light source.
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

        # XXX This is a temporary hack to make things not so gloomy until the
        # server starts telling us about light sources.
        self.addLight(StaticLight(Vector(5, 10, 5)))


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
        # XXX Dead code?
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

    @ivar CHUNK_GRANULARITY: A L{Vector} giving the dimensions of terrain data
        which will be received from the server.  Keeping this fixed means that
        only a single coordinate needs to be checked to determine if terrain
        data is needed for a prism of this size.

    @ivar environment: The L{game.environment.Environment} which is being
        displayed.
    @ivar clock: Something providing
        L{twisted.internet.interfaces.IReactorTime}.
    @ivar screen: The L{pygame.Surface} which will be drawn to.
    @ivar _paintCall: C{None} or the L{IDelayedCall} provider for a pending
        C{paint} call.
    @ivar controller: The current controller.

    @ivar display: Something like L{pygame.display}.
    @ivar event: Something like L{pygame.event}.

    @ivar _terrainCheck: A L{LoopingCall} to check check for missing terrain and
        request it from the server.

    @ivar _playerViews: A mapping from known L{Player} instances to
        corresponding L{PlayerView} instances which have been added to the
        scene.
    """
    screen = None
    _terrainCheck = None

    CHUNK_GRANULARITY = CHUNK_GRANULARITY


    def __init__(self,
                 environment,
                 clock=reactor,
                 display=pygame.display,
                 event=pygame.event):
        self.viewport = Viewport((0, 0), (800, 600))
        self.environment = environment
        self.environment.addObserver(self)
        self.clock = clock
        self.display = display
        self.controller = None
        self.event = event
        self.scene = Scene()
        self.scene.add(TerrainView(environment, loadImage))
        self.scene.camera = StaticCamera(Vector(0, 0, 0), Vector(0, 0, 0))
        self._playerViews = {}


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
                elif event.type == pygame.MOUSEBUTTONUP:
                    pygame.event.set_grab(not pygame.event.get_grab())
                    pygame.mouse.set_visible(not pygame.mouse.set_visible(True))


    # The interval at which to check to see if more terrain data must be
    # requested.
    TERRAIN_CHECK_INTERVAL = 2

    # The distance in chunks in each direction to look around the player's
    # position for more missing terrain to request.
    CHUNK_OFFSET = Vector(2, 0, 2)

    def _checkTerrain(self, player):
        """
        Examine the player's position and the currently known terrain data and
        sometimes request more terrain data from the server.
        """
        terrain = self.environment.terrain
        network = self.environment.network
        if network is None:
            return

        s = player.getPosition()

        g = self.CHUNK_GRANULARITY
        x = int(quantize(g.x, s.x))
        y = int(quantize(g.y, s.y))
        z = int(quantize(g.z, s.z))

        dx = int(self.CHUNK_OFFSET.x * g.x)
        dy = int(self.CHUNK_OFFSET.y * g.y)
        dz = int(self.CHUNK_OFFSET.z * g.z)
        for px in range(x - dx, x + dx + 1, int(g.x)):
            for py in range(y - dy, y + dy + 1, int(g.y)):
                for pz in range(z - dz, z + dz + 1, int(g.z)):

                    if px < 0 or py < 0 or pz < 0:
                        continue

                    if px >= terrain.voxels.shape[0] or \
                            py >= terrain.voxels.shape[1] or \
                            pz >= terrain.voxels.shape[2] or \
                            terrain.voxels[px, py, pz] == UNKNOWN:
                        # XXX Add an errback
                        network.callRemote(GetTerrain, x=px, y=py, z=pz)


    def submitTo(self, controller):
        """
        Specify the given controller as the one to receive further
        events.
        """
        self.controller = controller
        self._terrainCheck = LoopingCall(self._checkTerrain, controller.player)
        self._terrainCheck.clock = self.clock
        # XXX Needs an errback
        self._terrainCheck.start(self.TERRAIN_CHECK_INTERVAL)
        # XXX Next line untested
        self.scene.camera = FollowCamera(controller.player)


    def go(self):
        """
        Show this window.

        @return: A Deferred that fires when this window is closed by the user.
        """
        self.display.init()
        self.screen = self.display.set_mode(
            self.viewport.viewSize,
            pygame.locals.DOUBLEBUF | pygame.locals.OPENGL)
        self.viewport.initialize()

        self._renderCall = LoopingCall(self.paint)
        self._renderCall.start(1 / 60, now=False)
        self._inputCall = LoopingCall(self.handleInput)
        finishedDeferred = self._inputCall.start(0.04, now=False)
        finishedDeferred.addCallback(lambda ign: self._renderCall.stop())
        finishedDeferred.addCallback(lambda ign: self.display.quit())

        return finishedDeferred


    def stop(self):
        """
        Stop updating this window and handling events for it.
        """
        if self._terrainCheck is not None:
            self._terrainCheck.stop()
        self._inputCall.stop()


    def playerCreated(self, player):
        """
        Create a L{PlayerView}.
        """
        self._playerViews[player] = view = PlayerView(player)
        self.scene.add(view)


    def playerRemoved(self, player):
        """
        Remove a L{PlayerView}.
        """
        view = self._playerViews.pop(player)
        self.scene._items.remove(view)



class TerrainView(object):
    """
    A view for terrain over a tract of land.

    @type environment: L{Environment}
    @ivar environment: The game environment from which terrain will be rendered.

    @ivar loader: A callable like L{loadImage}.

    @ivar _images: A cache of L{pygame.Surface} instances, keyed on terrain
        types.  These images are the source for texture data for each type of
        terrain.
    """
    _files = {
        GRASS: 'grass.png',
        MOUNTAIN: 'mountain.png',
        DESERT: 'desert.png',
        WATER: 'water.png',
        }

    _texture = None

    _datapath = FilePath(gameFile).sibling('data')

    def __init__(self, environment, loader):
        self._images = {}
        self.loader = loader
        self._vbos = []
        if environment is not None:
            self._coord, self._ext = self._getTextureForTerrain()
            self.environment = environment
            self._surface = SurfaceMesh(
                environment.terrain, self._surfaceFactory, self._coord,
                self._ext)
            self.environment.terrain.addObserver(self._surface.changed)


    def _surfaceFactory(self):
        data = zeros((1000000, 5), 'f')
        result = SurfaceMeshVertices(VBO(data), data, 0)
        self._vbos.append(result)
        return result


    def _getImageForTerrain(self, terrainType):
        """
        @param terrainType: The terrain type.

        @rtype: L{Surface}
        @return: An image which represents the given C{terrainType}.
        """
        if terrainType not in self._images:
            image = self.loader(
                self._datapath.child(self._files[terrainType]))
            self._images[terrainType] = image
        return self._images[terrainType]


    def _createTexture(self):
        surface = self._textureImage
        width = surface.get_width()
        height = surface.get_height()
        raw = pygame.image.tostring(surface, "RGBA", 0)

        texture = glGenTextures(1)
        # glGenTextures fails by returning 0, particularly if there's no GL
        # context yet.
        assert texture != 0
        glBindTexture(GL_TEXTURE_2D, texture)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        glTexImage2D(
            GL_TEXTURE_2D, 0,
            GL_RGBA, width, height, 0,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            raw)

        return texture


    def _getTextureForTerrain(self):
        """
        Return a single texture containing image data for every terrain type, as
        well as a dictionary mapping each terrain type to the corresponding
        texture coordinates, and a float indicating the size of each terrain's
        area of the overall texture.
        """
        dimensions = int(len(self._files) ** 0.5) + 2
        surface = pygame.surface.Surface((64 * dimensions, 64 * dimensions))
        coordinates = {}

        types = self._files.iterkeys()

        for y in range(dimensions):
            for x in range(dimensions):
                try:
                    terrainType = types.next()
                except StopIteration:
                    break

                image = self._getImageForTerrain(terrainType)
                surface.blit(image, (x * 64, y * 64))
                coordinates[terrainType] = (x / dimensions, y / dimensions)

        self._textureImage = surface
        return coordinates, 1 / dimensions


    def paint(self):
        """
        For all of the known terrain, render whatever faces are exposed.
        """
        if self._texture is None:
            self._texture = self._createTexture()

        glBindTexture(GL_TEXTURE_2D, self._texture)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        for surface in self._vbos:
            vbo = surface.update
            length = surface.important
            vbo.bind()
            glVertexPointer(3, GL_FLOAT, 4 * 5, vbo)
            glTexCoordPointer(2, GL_FLOAT, 4 * 5, vbo + (4 * 3))
            glDrawArrays(GL_TRIANGLES, 0, length)
            vbo.unbind()
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        glBindTexture(GL_TEXTURE_2D, 0)



class PlayerView(record('player')):
    """
    View of a player.
    """
    def paint(self):
        glPushMatrix()

        position = self.player.getPosition()
        glTranslate(position.x, position.y, position.z)
        glRotate(self.player.orientation.y, 0.0, 1.0, 0.0)
        # Slide back because the pyramid below is centered at 0.5, 0, 0.5
        # instead of at the origin.  Without this it rotates around its corner
        # instead of around its center.
        glTranslate(-0.5, 0, -0.5)

        glColor(1.0, 1.0, 1.0)

        glBegin(GL_TRIANGLES)
        glVertex3f(0.5, 0.0, 0.5)
        glVertex3f(0.0, 1.0, 0.0)
        glVertex3f(1.0, 1.0, 0.0)

        glVertex3f(0.5, 0.0, 0.5)
        glVertex3f(1.0, 1.0, 0.0)
        glVertex3f(1.0, 1.0, 1.0)

        glVertex3f(0.5, 0.0, 0.5)
        glVertex3f(1.0, 1.0, 1.0)
        glVertex3f(0.0, 1.0, 1.0)

        glVertex3f(0.5, 0.0, 0.5)
        glVertex3f(0.0, 1.0, 1.0)
        glVertex3f(0.0, 1.0, 0.0)
        glEnd()

        glPopMatrix()

