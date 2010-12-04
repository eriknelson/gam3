"""
Tests for L{game.network} (Network support for Game).
"""

import numpy

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred
from twisted.internet.task import Clock

from game.test.util import (
    ArrayMixin, PlayerCreationMixin, PlayerVisibilityObserver)
from game.environment import Environment
from game.network import (Direction, Introduce, SetDirectionOf,
                          NetworkController, NewPlayer, SetMyDirection,
                          RemovePlayer, GetTerrain, SetTerrain, Terrain)
from game.direction import FORWARD, BACKWARD, LEFT, RIGHT
from game.terrain import (
    WATER, GRASS, DESERT, MOUNTAIN, loadTerrainFromString)
from game.vector import Vector


class DirectionArgumentTests(TestCase):
    """
    Tests for L{Direction}.
    """
    def test_cardinalConversion(self):
        """
        The cardinal directions should round trip through the L{Direction}
        argument.
        """
        argument = Direction()
        for direction in (FORWARD, BACKWARD, LEFT, RIGHT):
            netrepr = argument.toString(direction)
            self.assertIdentical(type(netrepr), str)
            self.assertEqual(argument.fromString(netrepr), direction)


    def test_intercardinalConversion(self):
        """
        The intercardinal directions should round trip through the L{Direction}
        argument.
        """
        argument = Direction()
        for latitudinalSign in (FORWARD, BACKWARD):
            for longitudinalSign in (LEFT, RIGHT):
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
        'x': -3.5,
        'y': 2.5,
        'z': 0.5}
    responseStrings = stringifyDictValues(responseObjects)

    argumentObjects = argumentStrings = {}



class NewPlayerCommandTests(CommandTestMixin, TestCase):
    """
    Tests for L{NewPlayer}.
    """

    command = NewPlayer

    argumentObjects = {
        'identifier': 123,
        'x': 505.5,
        'y': 23489.5,
        'z': -10.5,
        'speed': 3999}

    argumentStrings = stringifyDictValues(argumentObjects)

    responseObjects = responseStrings = {}



class TerrainArgumentTests(TestCase):
    """
    Tests for L{Terrain}, an AMP argument serializer for 3d numpy arrays.
    """
    data = ''.join(map(chr, range(2 * 3 * 4)))
    array = numpy.fromstring(data, 'b').reshape((2, 3, 4))
    serialized = {
        "voxels-dx": "2",
        "voxels-dy": "3",
        "voxels-dz": "4",
        "voxels-type": "int8",
        "voxels-data": data}
    del data

    def test_toBox(self):
        """
        L{Terrain.toBox} serializes the numpy array from C{objects} associated
        with the key C{name}.  It adds C{I{name}-dx}, C{I{name}-dy}, and
        C{I{name}-dz} keys to the C{strings} dict, with values representing the
        size of the array in each of those dimensions.  It adds a
        C{I{name}-type} key with the numpy array element type as a value.  It
        adds a C{I{name}-data} key with the raw array data as a value.
        """
        objects = {"voxels": self.array}
        strings = {}
        argument = Terrain()
        argument.toBox("voxels", strings, objects, None)
        self.assertEquals(strings, self.serialized)


    def test_fromBox(self):
        """
        L{Terrain.fromBox} reads the C{name}-prefixed I{dx}, I{dy}, I{dz},
        I{type}, and I{data} keys from the strings dict passed to it and
        constructs a numpy array with the indicated shape and type from the
        data.  The array is put into the objects dict associated with the
        C{name} key.
        """
        objects = {}
        argument = Terrain()
        argument.fromBox("voxels", self.serialized, objects, None)
        # Can't compare dicts directly, because numpy arrays are weird.
        self.assertEquals(objects.keys(), ["voxels"])
        self.assertTrue((objects["voxels"] == self.array).all())



class GetTerrainCommandTests(CommandTestMixin, TestCase):
    """
    Tests for L{GetTerrain}.
    """
    command = GetTerrain

    argumentObjects = {'x': 2, 'y': 7, 'z': 13}
    argumentStrings = {'x': '2', 'y': '7', 'z': '13'}

    responseObjects = responseStrings = {}



class SetTerrainCommandTests(CommandTestMixin, TestCase):
    """
    Tests for L{SetTerrain}.
    """

    command = SetTerrain

    _shape = (1, 2, 10)
    _data = range(10) + range(16, 26)
    argumentObjects = {
        'x': 393,
        'y': 292,
        'z': 12,
        'voxels': numpy.fromstring(
            ''.join(map(chr, _data)), 'b').reshape(_shape)
        }

    argumentStrings = {
        'x': '393',
        'y': '292',
        'z': '12',
        'voxels-dx': '1',
        'voxels-dy': '2',
        'voxels-dz': '10',
        'voxels-type': 'int8',
        'voxels-data': (
            '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09'
            '\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19'),
        }

    responseObjects = responseStrings = {}


    def test_parseArguments(self):
        """
        Parsing C{self.argumentStrings} should result in
        C{self.argumentObjects}.  Duplicated here to implement correct
        numpy.array comparison, since we cannot just use C{==}.
        """
        from twisted.protocols.amp import _stringsToObjects
        box = _stringsToObjects(self.argumentStrings,
                                self.command.arguments, None)
        voxels = box.pop("voxels")
        argumentObjects = self.argumentObjects.copy()
        expected = argumentObjects.pop("voxels")
        self.assertEquals(box, argumentObjects)
        self.assertTrue((voxels == expected).all())



class RemovePlayerCommandTests(CommandTestMixin, TestCase):
    """
    Tests for L{RemovePlayer}.
    """

    command = RemovePlayer

    responseObjects = responseStrings = {}

    argumentObjects = {'identifier': 123}
    argumentStrings = stringifyDictValues(argumentObjects)



class SetMyDirectionTests(CommandTestMixin, TestCase):
    """
    Tests for L{SetMyDirection}.
    """
    command = SetMyDirection

    argumentObjects = {'direction': RIGHT, 'y': 1.5}
    argumentStrings = {
        'direction': Direction().toString(RIGHT),
        'y': '1.5'}

    responseObjects = {'x': 32.5, 'y': 939.5, 'z': 5.5}
    responseStrings = stringifyDictValues(responseObjects)



class SetDirectionOfTests(CommandTestMixin, TestCase):
    """
    Tests for L{SetDirectionOf}.
    """

    command = SetDirectionOf

    argumentObjects = {
        'identifier': 595,
        'direction': RIGHT,
        'x': 939.5,
        'y': -93999.5,
        'z': 10.5,
        'orientation': 2.25}

    argumentStrings = stringifyDictValues(argumentObjects)
    argumentStrings['direction'] = Direction().toString(RIGHT)

    responseObjects = responseStrings = {}



class ControllerTests(TestCase, PlayerCreationMixin, ArrayMixin):
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
        self.player = self.makePlayer(Vector(1, 2, 3))
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


    def test_setDirectionOf(self):
        """
        When L{SetDirectionOf} is issued, the L{Player}'s direction, position,
        and orientation should be set.
        """
        self.controller.addModelObject(self.identifier, self.player)

        responder = self.controller.lookupFunction(SetDirectionOf.commandName)
        direction = Direction().toString(FORWARD)
        x, y, z = (234.5, 5985.5, 12.5)
        orientation = 3.5
        d = responder({
                'identifier': str(self.identifier),
                'direction': direction,
                'x': str(x),
                'y': str(y),
                'z': str(z),
                'orientation': str(orientation)})

        def gotDirectionSetting(ign):
            self.assertEquals(self.player.direction, FORWARD)
            self.assertEquals(self.player.getPosition(), Vector(x, y, z))
            self.assertEquals(self.player.orientation.y, orientation)
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
        x, y, z = (3, 2, 12)
        speed = 40
        granularity = 22
        environment = Environment(granularity, self.clock)
        observer = PlayerVisibilityObserver()
        environment.addObserver(observer)

        self.controller.createInitialPlayer(
            environment, self.identifier, Vector(x, y, z), speed)

        self.assertEqual(len(observer.createdPlayers), 1)
        self._assertThingsAboutPlayerCreation(
            environment, Vector(x, y, z), speed)


    def test_greetServer(self):
        """
        L{NetworkController.introduce} should send an L{Introduce} command to
        the server and handle the result by populating its model mapping with a
        new entry.
        """
        self.controller.modelObjects.clear()

        x, y, z = (3, 2, -5)
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
                         'y': y,
                         'z': z})

        self._assertThingsAboutPlayerCreation(
            self.controller.environment, Vector(x, y, z), speed)
        self.assertIsInstance(self.controller.environment, Environment)
        self.assertEquals(self.controller.environment.granularity, granularity)
        self.assertEquals(self.controller.environment.platformClock, self.clock)
        self.assertIdentical(
            self.controller.environment.network, self.controller)
        introduced.addCallback(
            self.assertIdentical, self.controller.environment)
        return introduced


    def test_movementDirectionChanged(self):
        """
        Change of direction of movement by model objects should be translated
        into a network call by L{NetworkController}.
        """
        self.controller.addModelObject(self.identifier, self.player)
        self.player.orientation.y = 2.0
        self.player.setDirection(FORWARD)
        self.assertEqual(len(self.calls), 1)
        result, command, kw = self.calls.pop(0)
        self.assertIdentical(command, SetMyDirection)
        self.assertEqual(kw, {"direction": FORWARD, "y": 2.0})


    def test_orientationDirectionChanged(self):
        """
        Change of direction of orientation by model objects should be translated
        into a network call by L{NetworkController}.
        """
        self.controller.addModelObject(self.identifier, self.player)
        self.player.turn(0.0, 1.5)
        self.assertEqual(len(self.calls), 1)
        result, command, kw = self.calls.pop(0)
        self.assertIdentical(command, SetMyDirection)
        self.assertEqual(kw, {"direction": None, "y": 1.5})


    def test_directionChangedResponse(self):
        """
        When the server responds to a L{SetMyDirection} command with new a
        position, the L{NetworkController} should update the L{Player}'s
        position.
        """
        self.controller.directionChanged(self.player)
        self.assertEquals(len(self.calls), 1)
        x, y, z = (123, 5398, 10.5)
        self.calls[0][0].callback({"x": x, "y": y, "z": z})
        self.assertEqual(self.player.getPosition(), Vector(x, y, z))


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
        x, y, z = (3, 500, 5)
        speed = 999
        d = responder({
                "identifier": "123", "x": str(x), "y": str(y), "z": str(z),
                "speed": str(speed)})
        def gotResult(ign):
            self.assertEqual(len(observer.createdPlayers), 1)
            player = observer.createdPlayers[0]
            self.assertEqual(player.getPosition(), Vector(x, y, z))
            self.assertEqual(player.speed, speed)
            obj = self.controller.objectByIdentifier(
                self.controller.identifierByObject(player))
            self.assertIdentical(obj, player)
        d.addCallback(gotResult)
        return d


    # XXX Fix test name and clarify docstring.
    def test_newPlayer2(self):
        """
        The L{NewPlayer} responder should not cause the
        L{NetworkController} to observe the new player.
        """
        self.controller.environment = Environment(10, self.clock)
        responder = self.controller.lookupFunction(NewPlayer.commandName)
        identifier = 123
        d = responder({"identifier": str(identifier),
                       "x": "1", "y": "2", "z": "3", "speed": "99"})
        def gotResult(ign):
            player = self.controller.objectByIdentifier(identifier)
            player.setDirection(RIGHT)
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
        self.controller.newPlayer(identifier, 23, 32, 13, 939)
        responder = self.controller.lookupFunction(RemovePlayer.commandName)
        d = responder({"identifier": str(identifier)})
        def gotResult(ignored):
            self.assertEqual(observer.removedPlayers, observer.createdPlayers)
            self.assertRaises(
                KeyError,
                self.controller.objectByIdentifier, identifier)
        d.addCallback(gotResult)
        return d


    def test_setTerrainAtOrigin(self):
        """
        L{NetworkController} should respond to the L{SetTerrain}
        command by updating its terrain model with the received data.
        """
        environment = self.controller.environment = Environment(10, self.clock)
        responder = self.controller.lookupFunction(SetTerrain.commandName)
        terrainData = loadTerrainFromString('G')
        terrainObjects = dict(x=0, y=0, z=0, voxels=terrainData)
        terrainStrings = SetTerrain.makeArguments(terrainObjects, None)
        d = responder(terrainStrings)
        def gotResult(ignored):
            self.assertEquals(
                environment.terrain.dict(), {(0, 0, 0): GRASS})
        d.addCallback(gotResult)
        return d


    def test_overwriteTerrain(self):
        """
        When L{NetworkController} receives a L{SetTerrain} which overlaps with
        existing terrain data, the existing data is overwritten.
        """
        environment = self.controller.environment = Environment(10, self.clock)
        environment.terrain.set(0, 0, 0, loadTerrainFromString('G'))
        responder = self.controller.lookupFunction(SetTerrain.commandName)
        terrainObjects = dict(x=0, y=0, z=0, voxels=loadTerrainFromString('M'))
        terrainStrings = SetTerrain.makeArguments(terrainObjects, None)
        d = responder(terrainStrings)
        def gotResult(ignored):
            self.assertEquals(
                environment.terrain.dict(), {(0, 0, 0): MOUNTAIN})
        d.addCallback(gotResult)
        return d


    def test_extendX(self):
        """
        When L{NetworkController} receives terrain in a L{SetTerrain} command
        which extends beyond the current maximum X coordinate, the terrain array
        is extended in the X direction to contain it.
        """
        environment = self.controller.environment = Environment(10, self.clock)
        environment.terrain.set(0, 0, 0, loadTerrainFromString('DG'))
        responder = self.controller.lookupFunction(SetTerrain.commandName)
        terrainObjects = dict(x=3, y=0, z=0, voxels=loadTerrainFromString('W'))
        terrainStrings = SetTerrain.makeArguments(terrainObjects, None)
        d = responder(terrainStrings)
        def gotResult(ignored):
            self.assertEquals(
                environment.terrain.dict(),
                {(0, 0, 0): DESERT, (1, 0, 0): GRASS, (3, 0, 0): WATER})
        d.addCallback(gotResult)
        return d


    def test_extendY(self):
        """
        When L{NetworkController} receives terrain in a L{SetTerrain} command
        which extends beyond the current maximum Y coordinate, the terrain array
        is extended in the Y direction to contain it.
        """
        environment = self.controller.environment = Environment(10, self.clock)
        environment.terrain.set(0, 0, 0, loadTerrainFromString('D\n\nG'))
        responder = self.controller.lookupFunction(SetTerrain.commandName)
        terrainObjects = dict(x=0, y=3, z=0, voxels=loadTerrainFromString('W'))
        terrainStrings = SetTerrain.makeArguments(terrainObjects, None)
        d = responder(terrainStrings)
        def gotResult(ignored):
            self.assertEquals(
                environment.terrain.dict(),
                {(0, 0, 0): GRASS, (0, 1, 0): DESERT, (0, 3, 0): WATER})
        d.addCallback(gotResult)
        return d


    def test_extendZ(self):
        """
        When L{NetworkController} receives terrain in a L{SetTerrain} command
        which extends beyond the current maximum Z coordinate, the terrain array
        is extended in the Z direction to contain it.
        """
        environment = self.controller.environment = Environment(10, self.clock)
        environment.terrain.set(0, 0, 0, loadTerrainFromString('D\nG'))
        responder = self.controller.lookupFunction(SetTerrain.commandName)
        terrainObjects = dict(x=0, y=0, z=3, voxels=loadTerrainFromString('W'))
        terrainStrings = SetTerrain.makeArguments(terrainObjects, None)
        d = responder(terrainStrings)
        def gotResult(ignored):
            self.assertEquals(
                environment.terrain.dict(),
                {(0, 0, 0): DESERT, (0, 0, 1): GRASS, (0, 0, 3): WATER})
        d.addCallback(gotResult)
        return d


    def test_preserveX(self):
        """
        When L{NetworkController} receives terrain in a L{SetTerrain} command
        which doesn't extend as far in the X direction as the existing terrain
        data, the existing terrain data beyond the new terrain data in the X
        direction is preserved.
        """
        environment = self.controller.environment = Environment(10, self.clock)
        environment.terrain.set(0, 0, 0, loadTerrainFromString('DG\n\nMW'))
        responder = self.controller.lookupFunction(SetTerrain.commandName)
        # XXX Would be better if this terrain type were unique to ensure the
        # right data ends up in the right place.  But we're out of terrain types
        # for now.
        terrainObjects = dict(x=0, y=2, z=0, voxels=loadTerrainFromString('D'))
        terrainStrings = SetTerrain.makeArguments(terrainObjects, None)
        d = responder(terrainStrings)
        def gotResult(ignored):
            self.assertEquals(
                environment.terrain.dict(),
                {(0, 0, 0): MOUNTAIN, (1, 0, 0): WATER,
                 (0, 1, 0): DESERT, (1, 1, 0): GRASS,
                 (0, 2, 0): DESERT})
        d.addCallback(gotResult)
        return d


    def test_preserveY(self):
        """
        When L{NetworkController} receives terrain in a L{SetTerrain} command
        which doesn't extend as far in the Y direction as the existing terrain
        data, the existing terrain data beyond the new terrain data in the Y
        direction is preserved.
        """
        environment = self.controller.environment = Environment(10, self.clock)
        environment.terrain.set(0, 0, 0, loadTerrainFromString('DG\n\nMW'))
        responder = self.controller.lookupFunction(SetTerrain.commandName)
        # XXX Unique terrain type
        terrainObjects = dict(x=2, y=0, z=0, voxels=loadTerrainFromString('M'))
        terrainStrings = SetTerrain.makeArguments(terrainObjects, None)
        d = responder(terrainStrings)
        def gotResult(ignored):
            self.assertEquals(
                environment.terrain.dict(),
                {(0, 0, 0): MOUNTAIN, (1, 0, 0): WATER,
                 (0, 1, 0): DESERT, (1, 1, 0): GRASS,
                 (2, 0, 0): MOUNTAIN})
        d.addCallback(gotResult)
        return d


    def test_preserveZ(self):
        """
        When L{NetworkController} receives terrain in a L{SetTerrain} command
        which doesn't extend as far in the Z direction as the existing terrain
        data, the existing terrain data beyond the new terrain data in the Z
        direction is preserved.
        """
        environment = self.controller.environment = Environment(10, self.clock)
        environment.terrain.set(0, 0, 0, loadTerrainFromString('DG\nMW'))
        responder = self.controller.lookupFunction(SetTerrain.commandName)
        # XXX Unique terrain type
        terrainObjects = dict(x=2, y=0, z=0, voxels=loadTerrainFromString('G'))
        terrainStrings = SetTerrain.makeArguments(terrainObjects, None)
        d = responder(terrainStrings)
        def gotResult(ignored):
            self.assertEquals(
                environment.terrain.dict(),
                {(0, 0, 0): DESERT, (1, 0, 0): GRASS,
                 (0, 0, 1): MOUNTAIN, (1, 0, 1): WATER,
                 (2, 0, 0): GRASS})
        d.addCallback(gotResult)
        return d

