from twisted.python.util import FancyEqMixin, FancyStrMixin

class Vector(FancyEqMixin, FancyStrMixin):
    """
    A coordinate in three dimensional space.
    """
    showAttributes = compareAttributes = ['x', 'y', 'z']

    def __init__(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)


    def __add__(self, other):
        return Vector(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z)


    def __mul__(self, other):
        """
        Implement multiplication by a scalar in the conventional manner.

        @type other: C{int} or C{float}
        @rtype: L{Vector}
        """
        return Vector(
            self.x * other,
            self.y * other,
            self.z * other)
