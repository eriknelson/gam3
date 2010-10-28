
"""
Common code for functional tests.
"""

class FunctionalTestMixin:
    def setUp(self):
        # XXX PRIVATE VARIABLE USAGE ZOMG
        print getattr(self, self._testMethodName).__doc__


    def tearDown(self):
        if not raw_input("Did it work?").lower().startswith('y'):
            self.fail("User specified test failure")



