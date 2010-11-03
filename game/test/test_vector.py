from twisted.trial.unittest import TestCase

from game.vector import Vector

class VectorTests(TestCase):
    """
    Tests for L{Vector}.
    """
    def test_attributes(self):
        """
        The three arguments passed to the L{Vector} initializer are bound to its
        C{x}, C{y}, and C{z} attributes.
        """
        v = Vector(1, 2, 3)
        self.assertEquals(v.x, 1)
        self.assertEquals(v.y, 2)
        self.assertEquals(v.z, 3)


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


    def test_equality(self):
        """
        Two L{Vector} instances with equal components are equal to each other.
        """
        v1 = Vector(1, 2, 3)
        v2 = Vector(1, 2, 3)
        self.assertTrue(v1 == v2)
        v3 = Vector(1, 2, 4)
        self.assertFalse(v1 == v3)
