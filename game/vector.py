from twisted.python.util import FancyEqMixin

from epsilon.structlike import record

class Vector(record("x y z"), FancyEqMixin):
    """
    A coordinate in three dimensional space.
    """
    compareAttributes = ['x', 'y', 'z']

    def __add__(self, other):
        return Vector(
            self.x + other.x,
            self.y + other.y,
            self.z + other.z)
