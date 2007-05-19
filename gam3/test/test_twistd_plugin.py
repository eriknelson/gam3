
"""
Tests for the twistd service plugin definition module.
"""

from zope.interface.verify import verifyObject

from twisted.trial.unittest import TestCase
from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin

from twisted.plugins.gam3_twistd import gam3plugin

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
        service = gam3plugin.makeService({})
        
