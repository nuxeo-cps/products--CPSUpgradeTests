# Upgrade from CPS 3.3.8
DB_NAME = 'cps338'

import os
import unittest

# Warning, nifty tapdance ahead:

# When you import testing, it sets testing home to 
# $SOFTWARE_HOME/lib/python/Testing
import Testing

# But we want it to be in a directory with our custom_zodb.py, so we set it, 
# but only after importing Testing (or it will be reset later).
import App.config
cfg = App.config.getConfiguration()
cfg.testinghome = os.path.join(os.path.dirname(__file__), DB_NAME)

# During the import of the ZopeLite module, the Zope Application will be
# started, and it will now use our testinghome, find our custom_zodb.py and
# use our custom ZODB.
# Actually, we import upgradetestcase, which in turn imports ZopeTestCase,
# which in turn imports ZopeLite, which in turns starts Zope.
from upgradetestcase import PreGenericSetupTestCase

# Tapdance ends.


class TestUpgrade(PreGenericSetupTestCase):

    db_dir = DB_NAME

    def test_upgrade(self):
        self._upgrade()
        self._verifyDocument()
        self._verifyPublishing()
        self._verifyCalendaring()
        self._checkSubGroupSupport()
                
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestUpgrade),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
