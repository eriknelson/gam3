# -*- test-case-name: gam3.test.test_twistd_plugin -*-

"""
Plugin hook module for twistd service.
"""

from os.path import join

from zope.interface import implements

from twisted.application.service import IServiceMaker
from twisted.application.internet import TCPServer
from twisted.plugin import IPlugin
from twisted.python.usage import Options, portCoerce

def _parseTerrain(map):
    from game.terrain import GRASS, MOUNTAIN, DESERT
    types = {'G': GRASS, 'M': MOUNTAIN, 'D': DESERT}
    result = {}
    for z, line in enumerate(map.strip().splitlines()[::-1]):
        for x, ch in enumerate(line):
            result[x, 0, z] = types[ch]
    return result


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
            ('port', 'p', 1337, 'TCP port number to listen on.', portCoerce),
            ('log-directory', 'l', None,
             'Directory to which to log protocol traffic.'),
            ('terrain', None, None,
             'Filename containing the terrain data to use.')]

    description = "Gam3 MMO server"

    tapname = "gam3"

    def makeService(self, options):
        """
        Create a service which will run a Gam3 server.

        @param options: mapping of configuration
        """
        from gam3.network import Gam3Factory
        from gam3.world import (
            TCP_SERVICE_NAME, GAM3_SERVICE_NAME, Gam3Service, World)
        from twisted.python.filepath import FilePath
        from twisted.internet import reactor
        from twisted.application.service import MultiService
        from twisted.protocols.policies import TrafficLoggingFactory

        world = World(granularity=100, platformClock=reactor)
        if options['terrain']:
            world.terrain.update(
                _parseTerrain(FilePath(options['terrain']).getContent()))

        service = MultiService()

        factory = Gam3Factory(world)
        if options['log-directory'] is not None:
            factory = TrafficLoggingFactory(
                factory, join(options['log-directory'], 'gam3'))

        tcp = TCPServer(options['port'], factory)
        tcp.setName(TCP_SERVICE_NAME)
        tcp.setServiceParent(service)

        gam3 = Gam3Service(world)
        gam3.setName(GAM3_SERVICE_NAME)
        gam3.setServiceParent(service)

        return service

gam3plugin = _Gam3Plugin()
