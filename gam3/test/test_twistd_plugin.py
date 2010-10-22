
"""
Tests for the twistd service plugin definition module.
"""

from os.path import join

from zope.interface.verify import verifyObject

from twisted.python.filepath import FilePath
from twisted.trial.unittest import TestCase
from twisted.application.service import IServiceMaker
from twisted.application.internet import TCPServer
from twisted.protocols.policies import TrafficLoggingFactory
from twisted.plugin import IPlugin

from twisted.plugins.gam3_twistd import gam3plugin
from gam3.network import Gam3Factory
from gam3.world import TCP_SERVICE_NAME, GAM3_SERVICE_NAME, Gam3Service, World

from game.terrain import GRASS, MOUNTAIN, DESERT


class TwistdPluginTests(TestCase):
    """
    Tests for the plugin object which adds a service to twistd.
    """
    def test_discoverability(self):
        """
        The plugin object should provide L{IPlugin} and L{IServiceMaker} so as
        to be discoverable by the Twisted plugin system when L{IServiceMaker}
        plugins are searched for.
        """
        verifyObject(IPlugin, gam3plugin)
        verifyObject(IServiceMaker, gam3plugin)


    def test_makeService(self):
        """
        L{Gam3Plugin.makeService} should return an L{IService} provider.
        """
        portNumber = 123
        service = gam3plugin.makeService({
                'port': portNumber,
                'log-directory': None,
                'terrain': None})
        tcp = service.getServiceNamed(TCP_SERVICE_NAME)
        self.assertTrue(isinstance(tcp, TCPServer))
        gotPortNumber, factory = tcp.args
        self.assertEqual(gotPortNumber, portNumber)
        self.assertTrue(isinstance(factory, Gam3Factory))
        self.assertTrue(isinstance(factory.world, World))

        gam3 = service.getServiceNamed(GAM3_SERVICE_NAME)
        self.assertTrue(isinstance(gam3, Gam3Service))
        self.assertIdentical(gam3.world, factory.world)


    def test_logging(self):
        """
        L{Gam3Plugin.makeService} should recognize logging configuration and
        wrap its factory with L{TrafficLoggingFactory}.
        """
        logDirectory = self.mktemp()
        service = gam3plugin.makeService({
                'port': 123,
                'log-directory': logDirectory,
                'terrain': None})
        tcp = service.getServiceNamed(TCP_SERVICE_NAME)
        portNumber, factory = tcp.args
        self.assertTrue(isinstance(factory, TrafficLoggingFactory))
        self.assertTrue(isinstance(factory.wrappedFactory, Gam3Factory))
        self.assertEqual(
            factory.logfilePrefix,
            join(logDirectory, 'gam3'))


    def test_imports(self):
        """
        Verify that the plugin module does not import gam3 at import time.
        """
        self.fail("This should really be implemented.")
    test_imports.todo = ("This should really be implemented to verify that "
                         "the plugin module does not import gam3 at import "
                         "time.")


    def test_world_construction(self):
        """
        The plugin should construct a World with appropriate defaults.
        """
        from twisted.internet import reactor
        service = gam3plugin.makeService({
                'port': 123,
                'log-directory': None,
                'terrain': None})
        world = service.getServiceNamed(GAM3_SERVICE_NAME).world
        self.assertEqual(world.granularity, 100)
        self.assertEqual(world.platformClock, reactor)


    def test_terrain(self):
        """
        If the terrain option is specified, terrain data is loaded from it.
        """
        terrain = self.mktemp()
        FilePath(terrain).setContent("GGG\nGGM\nGMM\nGMD\n")
        service = gam3plugin.makeService({
                "port": 123, 'log-directory': None, 'terrain': terrain})
        gam3 = service.getServiceNamed(GAM3_SERVICE_NAME)
        self.assertEquals(
            gam3.world.terrain,
            {(0, 192): GRASS, (64, 192): GRASS, (128, 192): GRASS,
             (0, 128): GRASS, (64, 128): GRASS, (128, 128): MOUNTAIN,
             (0, 64): GRASS, (64, 64): MOUNTAIN, (128, 64): MOUNTAIN,
             (0, 0): GRASS, (64, 0): MOUNTAIN, (128, 0): DESERT})
