#/usr/bin/env python
# -*- coding: utf-8 -*- 
import os
import sys
import unittest

from mavencoordtest import MavenCoordTest
from mavenparsertest import MavenParserTest
from mavenversiondbtest import MavenVersionDbTest
from mavenrepotest import MavenRepoTest

def suite():
  return unittest.TestSuite([
    unittest.TestLoader().loadTestsFromTestCase (MavenCoordTest),
    unittest.TestLoader().loadTestsFromTestCase (MavenParserTest),
    unittest.TestLoader().loadTestsFromTestCase (MavenVersionDbTest),
    unittest.TestLoader().loadTestsFromTestCase (MavenRepoTest)
  ])

if __name__ == '__main__':
  runner = unittest.TextTestRunner()
  testSuite = suite()
  runner.run (testSuite)
