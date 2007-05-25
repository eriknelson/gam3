"""
Tests for L{game.network} (Network support for Game).
"""

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred
from twisted.internet.task import Clock

from game.test.util import PlayerCreationMixin, PlayerVisibilityObserver
from game.environment import Environment
from game.network import (Direction, Introduce, SetPositionOf, SetDirectionOf,
                          NetworkController, NewPlayer, SetMyDirection,
                          RemovePlayer)
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



class CommandTestMixin(object):
    """
    Mixin for testcases for serialization and parsing of Commands.

    @cvar command: L{Command} subclass to test.

    @type argumentObjects: L{dict}
    @cvar argumentObjects: The unserialized forms of arguments matching the
        argument schema of your Command.

    @type argumentStrings: L{dict}
    @cvar argumentStrings: The serialized forms of arguments matching the
        argument schema of your Command.

    @type responseObjects: L{dict}
    @cvar responseObjects: The unserialized forms of responses matching the
        response schema of your Command.

    @type responseStrings: L{dict}
    @cvar responseStrings: The serialized forms of responses matching the
        response schema of your Command.
    """

    def test_makeResponse(self):
        """
        C{self.responseObjects} should serialize to C{self.responseStrings}.
        """
        box = self.command.makeResponse(self.responseObjects, None)
        self.assertEqual(box, self.responseStrings)


    def test_parseResponse(self):
        """
        C{self.responseStrings} should parse to C{self.responseObjects}.
        """
        from twisted.protocols.amp import _stringsToObjects
        objects = _stringsToObjects(self.responseStrings,
                                    self.command.response, None)
        self.assertEqual(objects, self.responseObjects)


    def test_makeArguments(self):
        """
        C{self.argumentObjects} should serialize to C{self.argumentStrings}.
        """
        from twisted.protocols.amp import _objectsToStrings
        strings = _objectsToStrings(self.argumentObjects,
                                    self.command.arguments, {}, None)
        self.assertEqual(strings, self.argumentStrings)


    def test_parseArguments(self):
        """
        Parsing C{self.argumentStrings} should result in
        C{self.argumentObjects}.
        """
        from twisted.protocols.amp import _stringsToObjects
        box = _stringsToObjects(self.argumentStrings,
                                self.command.arguments, None)
        self.assertEqual(box, self.argumentObjects)



def stringifyDictValues(schema):
    """
    Return a dict like C{schema} but whose values have been str()ed.
    """
    return dict([(k, str(v)) for k, v in schema.items()])



class IntroduceCommandTests(CommandTestMixin, TestCase):
    """
    Tests for L{Introduce}.
    """

    command = Introduce

    responseObjects = {
        'identifier': 123,
        'granularity': 20,
        'speed': 12,
        'x': -3,
        'y': 2}
    responseStrings = stringifyDictValues(responseObjects)

    argumentObjects = argumentStrings = {}



class NewPlayerCommandTests(CommandTestMixin, TestCase):
    """
    Tests for L{NewPlayer}.
    """

    command = NewPlayer

    argumentObjects = {
        'identifier': 123,
        'x': 505,
        'y': 23489,
        'speed': 3999}

    argumentStrings = stringifyDictValues(argumentObjects)

    responseObjects = responseStrings = {}



class RemovePlayerCommandTests(CommandTestMixin, TestCase):
    """
    Tests for L{RemovePlayer}.
    """

    command = RemovePlayer

    responseObjects = responseStrings = {}

    argumentObjects = {'identifier': 123}
    argumentStrings = {'identifier': '123'}



class SetMyDirectionTests(CommandTestMixin, TestCase):
    """
    Tests for L{SetMyDirection}.
    """
    command = SetMyDirection

    argumentObjects = {'direction': WEST}
    argumentStrings = {'direction': Direction().toString(WEST)}

    responseObjects = {'x': 32, 'y': 939}
    responseStrings = {'x': '32', 'y': '939'}



class SetDirectionOfTests(CommandTestMixin, TestCase):
    """
    Tests for L{SetDirectionOf}.
    """

    command = SetDirectionOf

    argumentObjects = {
        'identifier': 595,
        'direction': WEST,
        'x': 939,
        'y': -93999}

    argumentStrings = stringifyDictValues(argumentObjects)
    argumentStrings['direction'] = Direction().toString(WEST)

    responseObjects = responseStrings = {}



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
        When L{SetDirectionOf} is issued, the L{Player}'s direction and
        position should be set.
        """
        self.controller.addModelObject(self.identifier, self.player)

        responder = self.controller.lookupFunction(SetDirectionOf.commandName)
        direction = Direction().toString(NORTH)
        x, y = (234, 5985)
        d = responder({
                'identifier': str(self.identifier),
                'direction': direction,
                'x': str(x),
                'y': str(y)})

        def gotDirectionSetting(ign):
            self.assertEqual(self.player.direction, NORTH)
            self.assertEqual(self.player.getPosition(), (x, y))
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
        observer = PlayerVisibilityObserver()
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
        self.assertIdentical(command, SetMyDirection)
        self.assertEqual(kw, {"direction": NORTH})


    def test_directionChangedResponse(self):
        """
        When the server responds to a L{SetMyDirection} command with new a
        position, the L{NetworkController} should update the L{Player}'s
        position.
        """
        self.controller.directionChanged(self.player)
        self.assertEquals(len(self.calls), 1)
        x, y = (123, 5398)
        self.calls[0][0].callback({"x": x, "y": y})
        self.assertEqual(self.player.getPosition(), (x, y))


    def test_newPlayer(self):
        """
        L{NetworkController} should respond to L{NewPlayer} commands
        by introducing a new L{Player} object to the L{Environment}
        and registering the L{Player}'s identifier.
        """
        observer = PlayerVisibilityObserver()
        self.controller.environment = Environment(10, self.clock)
        self.controller.environment.addObserver(observer)
        responder = self.controller.lookupFunction(NewPlayer.commandName)
        x, y = (3, 500)
        speed = 999
        d = responder({"identifier": "123", "x": str(x), "y": str(y),
                       "speed": str(speed)})
        def gotResult(ign):
            self.assertEqual(len(observer.createdPlayers), 1)
            player = observer.createdPlayers[0]
            self.assertEqual(player.getPosition(), (x, y))
            self.assertEqual(player.speed, speed)
            obj = self.controller.objectByIdentifier(
                self.controller.identifierByObject(player))
            self.assertIdentical(obj, player)
        d.addCallback(gotResult)
        return d


    def test_newPlayer(self):
        """
        The L{NewPlayer} responder should not cause the
        L{NetworkController} to observe the new player.
        """
        self.controller.environment = Environment(10, self.clock)
        responder = self.controller.lookupFunction(NewPlayer.commandName)
        identifier = 123
        d = responder({"identifier": str(identifier),
                       "x": "1", "y": "2", "speed": "99"})
        def gotResult(ign):
            player = self.controller.objectByIdentifier(identifier)
            player.setDirection(WEST)
            self.assertEqual(self.calls, [])
        d.addCallback(gotResult)
        return d


    def test_removePlayer(self):
        """
        L{NetworkController} should respond to L{RemovePlayer}
        commands by removing the identified L{Player} object from the
        L{Environment} and forgetting the L{Player}'s identifier.
        """
        environment = Environment(10, self.clock)
        self.controller.environment = environment
        observer = PlayerVisibilityObserver()
        environment.addObserver(observer)
        identifier = 123
        self.controller.newPlayer(identifier, 23, 32, 939)
        responder = self.controller.lookupFunction(RemovePlayer.commandName)
        d = responder({"identifier": str(identifier)})
        def gotResult(ignored):
            self.assertEqual(observer.removedPlayers, observer.createdPlayers)
            self.assertRaises(
                KeyError,
                self.controller.objectByIdentifier, identifier)
        d.addCallback(gotResult)
        return d