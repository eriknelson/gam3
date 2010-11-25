
"""
Generally useful APIs related to unit tests.
"""

class ArrayMixin:
    """
    Mixin for TestCase subclasses which make assertions about numpy arrays.
    """
    def assertArraysEqual(self, a, b):
        """
        Verify that the shape, type, and contents of a and b are the same.
        """
        self.assertEquals(a.shape, b.shape)
        self.assertEquals(a.dtype, b.dtype)
        self.assertTrue((a == b).all())


