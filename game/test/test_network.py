"""
Tests for L{game.network} (Network support for Game).
"""

from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred

from game.test.util import PlayerCreationMixin
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
        self.controller = NetworkController()
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


    def test_greetServer(self):
        """
        L{NetworkController.introduce} should send an L{Introduce} command to
        the server and handle the result by populating its model mapping with a
        new entry.
        """
        self.controller.modelObjects.clear()

        d = self.controller.introduce()
        self.assertEqual(len(self.calls), 1)
        result, command, kw = self.calls.pop()
        self.assertIdentical(command, Introduce)
        self.assertEqual(kw, {})
        self.assertEqual(self.controller.modelObjects, {})
        result.callback({'identifier': self.identifier})
        self.assertEqual(
            self.controller.modelObjects, {self.identifier: self.player})


    def test_directionChanged(self):
        """
        Change of direction by model objects should be translated into a
        network call by L{NetworkController}.
        """
        self.controller.addModelObject(self.identifier, self.player)
        self.player.setDirection(NORTH)
        self.assertEqual(
            self.calls,
            [(SetDirectionOf, {"identifier": self.identifier,
                               "direction": NORTH})])


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

