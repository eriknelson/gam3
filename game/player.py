# -*- test-case-name: game.test.test_player -*-

class Player(object):
    """
    An object with a position.

    @ivar position: A tuple of (x,y), specifying position of player.
    """

    def __init__(self, position):
        self.position = position

    def move(self, offset):
        """
        Add the given offset to the current position.

        @param offset: The vector to add to this player's current position.
        """
        posx, posy = self.position
        self.position = (posx + offset[0], posy + offset[1])
