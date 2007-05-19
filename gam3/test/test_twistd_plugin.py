
"""
Tests for the twistd service plugin definition module.
"""

from zope.interface.verify import verifyObject

from twisted.trial.unittest import TestCase
from twisted.application.service import IServiceMaker
from twisted.application.internet import TCPServer
from twisted.plugin import IPlugin

from twisted.plugins.gam3_twistd import gam3plugin
from gam3.network import Gam3Factory
from gam3.world import World


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
        service = gam3plugin.makeService({'port': portNumber})
        self.assertTrue(isinstance(service, TCPServer))
        gotPortNumber, factory = service.args
        self.assertEqual(gotPortNumber, portNumber)
        self.assertTrue(isinstance(factory, Gam3Factory))
        self.assertTrue(isinstance(factory.world, World))


    def test_imports(self):
        """
        Verify that the plugin module does not import gam3 at import time.
        """
        self.fail("This should really be implemented.")
    test_imports.todo = ("This should really be implemented to verify that "
                         "the plugin module does not import gam3 at import "
                         "time.")
