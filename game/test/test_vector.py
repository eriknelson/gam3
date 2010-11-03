from twisted.trial.unittest import TestCase

from game.vector import Vector

class VectorTests(TestCase):
    """
    Tests for L{Vector}.
    """
    def test_attributes(self):
        """
        The three arguments passed to the L{Vector} initializer are bound to its
        C{x}, C{y}, and C{z} attributes.  The attributes are always of type
        C{float} even if C{int} are passed to the initializer.
        """
        v = Vector(1, 2, 3)
        self.assertEquals(v.x, 1)
        self.assertEquals(v.y, 2)
        self.assertEquals(v.z, 3)
        self.assertIsInstance(v.x, float)
        self.assertIsInstance(v.y, float)
        self.assertIsInstance(v.z, float)


    def test_repr(self):
        """
        The string representation of a L{Vector} instance returned by L{repr}
        includes the names and values of each of its three attributes, and
        identifies the type itself as well.
        """
        self.assertEquals(
            repr(Vector(1.5, 2.5, -3.5)), "<Vector x=1.5 y=2.5 z=-3.5>")


    def test_addition(self):
        """
        The result of adding two L{Vector} instances is a L{Vector} with
        components equal to the sum of the components of the operands.
        """
        v1 = Vector(1, 2, 3)
        v2 = Vector(2, -1, 5)
        v3 = v1 + v2
        self.assertEquals(v3.x, 3)
        self.assertEquals(v3.y, 1)
        self.assertEquals(v3.z, 8)


    def test_multiplication(self):
        """
        The result of multiplying a L{Vector} by a number is a L{Vector} in the
        same direction as the original but with a magnitude greater by a factor
        of the multiplier.
        """
        v1 = Vector(1, 2, 3)
        v2 = v1 * 2.5
        self.assertEquals(v2, Vector(2.5, 5, 7.5))


    def test_equality(self):
        """
        Two L{Vector} instances with equal components are equal to each other.
        """
        v1 = Vector(1, 2, 3)
        v2 = Vector(1, 2, 3)
        self.assertTrue(v1 == v2)
        v3 = Vector(1, 2, 4)
        self.assertFalse(v1 == v3)
