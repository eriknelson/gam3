# -*- test-case-name: game.test.test_player -*-

class Player(object):
    """
    An object with a position.

    @ivar position: A tuple of (x,y), specifying position of player.

    @ivar observers: A list of objects which will be notified about state
    changes on this instance.
    """

    def __init__(self, position):
        self.position = position
        self.observers = []


    def move(self, offset):
        """
        Add the given offset to the current position.

        @param offset: The vector to add to this player's current position.
        """
        posx, posy = self.position
        self.position = (posx + offset[0], posy + offset[1])
        for observer in self.observers:
            observer.moved(self, (posx, posy))


    def addObserver(self, observer):
        """
        Notify the given object when this player's position changes.
        """
        self.observers.append(observer)
