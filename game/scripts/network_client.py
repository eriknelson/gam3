# -*- test-case-name: game.test.test_script -*-

"""
A basic script which connects a dumb client to a dumb server.
"""

import sys

from epsilon.structlike import record

from twisted.internet import reactor
from twisted.python import log

from game.ui import UI


NetworkClientBase = record('log reactor uiFactory',
                           log=log, reactor=reactor, uiFactory=UI)

class NetworkClient(NetworkClientBase):
    """
    An object which starts the Game client and connects it to a remote
    Game server.

    See L{run}.

    @ivar log: An object like L{twisted.python.log}
    @ivar reactor: An object like L{twisted.internet.reactor}
    @ivar uiFactory: An object like L{game.ui.UI}
    """

    def run(self, host, port):
        """
        Parse the given list of command line arguments and start up
        the Game client.

        @type arguments: L{list} of L{str}s
        @param arguments: Command-line arguments. The first should
            be a hostname and the second should be a port number.
        """
        # XXX TODO: reactor.stop on errback from start() But do it in
        # a way that will work if the errback is synchronous
        self.log.startLogging(sys.stdout)
        d = self.uiFactory().start((host, int(port)))
        d.addErrback(self.log.err, "Problem running UI")
        d.addCallback(lambda ignored: self.reactor.stop())
        self.reactor.run()

    def printUsage(self, commandLineArguments):
        """
        Print the command line usage of the client.
        """
        if len(commandLineArguments) <= 0:
            name = "NetworkClient"
        else:
            name = commandLineArguments[0]
        print "Game network client usage:"
        print "%s HOST PORT" % name

    def main(self, commandLineArguments):
        """
        Parse the given list of command line arguments and start up
        the Game client.
        """
        if len(commandLineArguments) < 3:
            self.printUsage(commandLineArguments)
            sys.exit(-1)
        host, port = commandLineArguments[1:]
        port = int(port)
        self.run(host, port)
