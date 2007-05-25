"""
Tests for Game scripts.
"""

import sys

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred
from twisted.python.failure import Failure
from twisted.python import log
from twisted.internet import reactor

from game.ui import UI
from game.scripts.network_client import NetworkClient


class DoubleLogModule(object):
    """
    A thing which looks like some of the L{twisted.python.log} module.

    @ivar messages: A list of arguments passed to L{msg}.
    @ivar errors: A list of arguments passed to L{err}.
    @ivar logFiles: A list of arguments passed to L{startLogging}.
    """

    def __init__(self):
        self.messages = []
        self.errors = []
        self.logFiles = []
        self.msg = self.messages.append
        self.err = self.errors.append
        self.startLogging = self.logFiles.append



class DoubleReactor(object):
    """
    A thing which has a L{run} method.

    @ivar runs: The number of times L{run} has been called.
    """

    def __init__(self):
        self.runs = 0


    def run(self):
        """
        Record an attempt to run the reactor.
        """
        self.runs += 1



class DoubleUI(object):
    """
    A thing which looks like L{game.ui.UI}.

    @ivar starts: Mapping of tuples of host and port to L{Deferred}s.
    """

    def __init__(self):
        self.starts = {}


    def start(self, (hostname, port)):
        """
        Record an attempt to start the game

        @return: A L{Deferred}.
        """
        d = Deferred()
        self.starts[hostname, port] = d
        return d



class NetworkClientTest(TestCase):
    """
    Tests for the simple network-client script.
    """

    def setUp(self):
        """
        Create a double logger, a double reactor, and a double UI, and
        a L{NetworkClient}.
        """
        self.logger = DoubleLogModule()
        self.reactor = DoubleReactor()
        self.ui = DoubleUI()
        self.networkClient = NetworkClient(
            log=self.logger, reactor=self.reactor, uiFactory=lambda: self.ui)


    def test_main(self):
        """
        There should be a method which takes command line arguments
        and runs the network client in an appropriate environment.
        """
        host = 'example.com'
        port = 1337
        self.networkClient.main(['network-client.py', host, str(port)])
        self.assertEqual(self.logger.logFiles, [sys.stdout])
        self.assertEqual(self.reactor.runs, 1)
        self.assertEqual(self.ui.starts.keys(), [(host, port)])


    def test_logErrors(self):
        """
        If the deferred returned from L{UI.start} should error back,
        the error should be logged.
        """
        self.networkClient.run('host', 123)
        e = Exception("OH NOES!")
        self.ui.starts[('host', 123)].errback(e)
        self.assertEqual(len(self.logger.errors), 1)
        error = self.logger.errors[0]
        self.assertIdentical(error.value, e)


    def test_defaults(self):
        """
        L{NetworkClient} should not require arguments to instantiate,
        and should have reasonable defaults.
        """
        client = NetworkClient()
        self.assertIdentical(client.log, log)
        self.assertIdentical(client.reactor, reactor)
        self.assertIdentical(client.uiFactory, UI)

