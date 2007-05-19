# -*- test-case-name: gam3.test.test_twistd_plugin -*-

"""
Plugin hook module for twistd service.
"""

from zope.interface import implements

from twisted.application.service import IServiceMaker
from twisted.application.internet import TCPServer
from twisted.plugin import IPlugin
from twisted.python.usage import Options, portCoerce

class _Gam3Plugin(object):
    """
    Trivial glue class to expose a twistd service.
    """
    implements(IPlugin, IServiceMaker)

    class options(Options):
        """
        Gam3 twistd command line options.
        """
        optParameters = [
            ('port', 'p', 1337, 'TCP port number to listen on.', portCoerce)]

    description = "Gam3 MMO server"

    tapname = "gam3"

    def makeService(self, options):
        """
        Create a service which will run a Gam3 server.

        @param options: mapping of configuration
        """
        from gam3.network import Gam3Factory
        from gam3.world import World
        from twisted.internet import reactor
        world = World(granularity=100, platformClock=reactor)
        return TCPServer(options['port'], Gam3Factory(world))

gam3plugin = _Gam3Plugin()
