"""
Tests for L{game.network} (Network support for Game).
"""

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred
from twisted.internet.task import Clock

from game.test.util import PlayerCreationMixin, PlayerCreationObserver
from game.environment import Environment
from game.network import (Direction, Introduce, SetPositionOf, SetDirectionOf,
                          NetworkController)
from game.direction import NORTH, SOUTH, EAST, WEST


class DirectionArgumentTests(TestCase):
    """
    Tests for L{Direction}.
    """
    def test_cardinalConversion(self):
        """
        The cardinal directions should round trip through the L{Complex}
        argument.
        """
        argument = Direction()
        for direction in (NORTH, SOUTH, EAST, WEST):
            netrepr = argument.toString(direction)
            self.assertIdentical(type(netrepr), str)
            self.assertEqual(argument.fromString(netrepr), direction)


    def test_intercardinalConversion(self):
        """
        The intercardinal directions should round trip through the L{Complex}
        argument.
        """
        argument = Direction()
        for latitudinalSign in (NORTH, SOUTH):
            for longitudinalSign in (EAST, WEST):
                direction = latitudinalSign + longitudinalSign
                netrepr = argument.toString(direction)
                self.assertIdentical(type(netrepr), str)
                self.assertEqual(argument.fromString(netrepr), direction)

    def test_stationality(self):
        """
        Direction should be able to deal with C{None} as a direction,
        which means "not moving".
        """
        argument = Direction()
        self.assertIdentical(argument.fromString(argument.toString(None)), None)



class IntroduceCommandTests(TestCase):
    """
    Tests for L{Introduce}.
    """
    def test_makeResponse(self):
        """
        L{Introduce.makeResponse} should convert a mapping of structured data
        into an L{AmpBox}.
        """
        identifier = 123
        granularity = 20
        speed = 12
        x = -3
        y = 2
        box = Introduce.makeResponse({'identifier': identifier,
                                      'granularity': granularity,
                                      'speed': speed,
                                      'x': x,
                                      'y': y}, None)
        self.assertEqual(
            box,
            {'identifier': str(identifier),
             'granularity': str(granularity),
             'speed': str(speed),
             'x': str(x),
             'y': str(y)})


    def test__objectsToStrings(self):
        """
        Holy shit!  Use private functionality from amp to test that responses
        are parsed properly.  See <trac://twisted/ticket/2657>.
        """
        # Holy shit!
        from twisted.protocols.amp import _stringsToObjects

        identifier = 123
        granularity = 20
        speed = 12
        x = -3
        y = 2

        objects = _stringsToObjects({'identifier': str(identifier),
                                     'granularity': str(granularity),
                                     'speed': str(speed),
                                     'x': str(x),
                                     'y': str(y)},
                                    Introduce.response,
                                    None)
        self.assertEqual(
            objects,
            {'identifier': identifier,
             'granularity': granularity,
             'speed': speed,
             'x': x,
             'y': y})



class ControllerTests(TestCase, PlayerCreationMixin):
    """
    L{NetworkController} takes network input and makes local changes to model
    objects.

    @ivar calls: A list of three-tuples consisting of a Deferred, a command
        subclass, and a dictionary of keyword arguments representing attempted
        Command invocations.

    """
    def setUp(self):
        self.calls = []
        self.identifier = 123
        self.player = self.makePlayer((1, 2))
        self.clock = Clock()
        self.controller = NetworkController(self.clock)
        self.controller.callRemote = self.callRemote


    def callRemote(self, commandType, **kw):
        """
        Record an attempt to invoke a remote command.
        """
        result = Deferred()
        self.calls.append((result, commandType, kw))
        return result


    def test_addModelObject(self):
        """
        L{NetworkController.addModelObject} should add a new item to the model
        objects mapping.
        """
        self.controller.addModelObject(self.identifier, self.player)
        self.assertEqual(
            self.controller.modelObjects, {self.identifier: self.player})


    def test_objectByIdentifier(self):
        """
        L{NetworkController.objectByIdentifier} should locate the correct
        object based on the mapping it maintains between objects and object
        identifiers.
        """
        self.controller.addModelObject(self.identifier, self.player)
        self.assertIdentical(
            self.controller.objectByIdentifier(self.identifier),
            self.player)


    def test_unknownObjectIdentifier(self):
        """
        L{NetworkController.objectByIdentifier} should raise L{KeyError} when
        given an identifier which corresponds to no model object.
        """
        self.assertRaises(
            KeyError,
            self.controller.objectByIdentifier, self.identifier)


    def test_identifierByObject(self):
        """
        L{NetworkController.identifierByObject} should locate the correct
        network identifier based on the reverse mapping it maintains between
        objects and object identifiers.
        """
        self.controller.addModelObject(self.identifier, self.player)
        self.assertEqual(
            self.controller.identifierByObject(self.player),
            self.identifier)


    def test_unknownObject(self):
        """
        L{NetworkController.identifierByObject} should raise L{ValueError} when
        given an object with no associated network identifier.
        """
        self.assertRaises(
            ValueError,
            self.controller.identifierByObject, self.player)


    def test_setPositionOf(self):
        """
        When L{SetPositionOf} is issued the L{Player}'s position should be set.
        """
        self.controller.addModelObject(self.identifier, self.player)

        x = str(23)
        y = str(32)
        identifier = str(self.identifier)
        responder = self.controller.lookupFunction(SetPositionOf.commandName)
        d = responder({'identifier': identifier, 'x': x, 'y': y})

        def gotPositionSetting(ign):
            self.assertEqual(self.player.getPosition(), (int(x), int(y)))
        d.addCallback(gotPositionSetting)
        return d


    def test_setDirectionOf(self):
        """
        When L{SetDirectionOf} is issued, the L{Player}'s direction should be
        set.
        """
        self.controller.addModelObject(self.identifier, self.player)

        responder = self.controller.lookupFunction(SetDirectionOf.commandName)
        direction = Direction().toString(NORTH)
        d = responder({
                'identifier': str(self.identifier),
                'direction': direction})

        def gotDirectionSetting(ign):
            self.assertEqual(self.player.direction, NORTH)
        d.addCallback(gotDirectionSetting)
        return d


    def _assertThingsAboutPlayerCreation(self, environment, position, speed):
        player = self.controller.modelObjects[self.identifier]
        self.assertEqual(player.getPosition(), position)
        self.assertEqual(player.speed, speed)
        self.assertEqual(player.seconds, environment.seconds)
        self.assertIdentical(environment.initialPlayer, player)


    def test_createInitialPlayer(self):
        """
        L{NetworkController._createInitialPlayer} should create the player
        object for this client.
        """
        x, y = (3, 2)
        speed = 40
        granularity = 22
        environment = Environment(granularity, self.clock)
        observer = PlayerCreationObserver()
        environment.addObserver(observer)

        self.controller.createInitialPlayer(
            environment, self.identifier, (x, y), speed)

        self.assertEqual(len(observer.createdPlayers), 1)
        player = observer.createdPlayers.pop()
        self._assertThingsAboutPlayerCreation(
            environment, (x, y), speed)


    def test_greetServer(self):
        """
        L{NetworkController.introduce} should send an L{Introduce} command to
        the server and handle the result by populating its model mapping with a
        new entry.
        """
        self.controller.modelObjects.clear()

        x, y = (3, 2)
        speed = 40
        granularity = 22
        introduced = self.controller.introduce()
        self.assertEqual(len(self.calls), 1)
        result, command, kw = self.calls.pop()
        self.assertIdentical(command, Introduce)
        self.assertEqual(kw, {})
        self.assertEqual(self.controller.modelObjects, {})
        self.assertIdentical(self.controller.environment, None)

        result.callback({'identifier': self.identifier,
                         'granularity': granularity,
                         'speed': speed,
                         'x': x,
                         'y': y})

        self._assertThingsAboutPlayerCreation(
            self.controller.environment, (x, y), speed)
        self.assertTrue(isinstance(self.controller.environment, Environment))
        self.assertEqual(self.controller.environment.granularity, granularity)
        self.assertEqual(self.controller.environment.platformClock, self.clock)
        introduced.addCallback(self.assertIdentical,
                               self.controller.environment)
        return introduced


    def test_directionChanged(self):
        """
        Change of direction by model objects should be translated into a
        network call by L{NetworkController}.
        """
        self.controller.addModelObject(self.identifier, self.player)
        self.player.setDirection(NORTH)
        self.assertEqual(len(self.calls), 1)
        result, command, kw = self.calls.pop(0)
        self.assertIdentical(command, SetDirectionOf)
        self.assertEqual(
            kw,
            {"identifier": self.identifier,
             "direction": NORTH})



class MockNetworkController(object):
    """
    A thing that looks like L{NetworkController}.

    """

    def __init__(self, modelObjects):
        self.calls = []
        self.modelObjects = modelObjects


    def identifierByObject(self, modelObject):
        for identifier, object in self.modelObjects.iteritems():
            if object is modelObject:
                return identifier
        raise ValueError("identifierByObject passed unknown model object")



class ObserverTests(TestCase, PlayerCreationMixin):
    """
    Tests for the bit which tells the network about what is happening to the
    L{Player} locally, which isL{NetworkPlayerObserver}.
    """

