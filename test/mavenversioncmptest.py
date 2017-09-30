#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import os,sys
import unittest

sys.path.append (os.path.join (os.path.dirname (__file__), '..'))

from mavencoord import MavenCoord
import mavenversioncmp as vercmp

class MavenVersionCompareTest (unittest.TestCase):
  
  def testGetCanonical (self):
    (major, minor, rev, qualifier, build) = vercmp.getCanonical ('')
    self.assertEquals (major, 0)
    self.assertEquals (minor, 0)
    self.assertEquals (rev, 0)
    self.assertEquals (qualifier, '')
    self.assertEquals (build, 0)
    
    (major, minor, rev, qualifier, build) = vercmp.getCanonical ('1.2')
    self.assertEquals (major, 1)
    self.assertEquals (minor, 2)
    self.assertEquals (rev, 0)
    self.assertEquals (qualifier, '')
    self.assertEquals (build, 0)
    
    (major, minor, rev, qualifier, build) = vercmp.getCanonical ('121.2.78')
    self.assertEquals (major, 121)
    self.assertEquals (minor, 2)
    self.assertEquals (rev, 78)
    self.assertEquals (qualifier, '')
    self.assertEquals (build, 0)
    
    (major, minor, rev, qualifier, build) = vercmp.getCanonical ('121.2.78-SNAPSHOT')
    self.assertEquals (major, 121)
    self.assertEquals (minor, 2)
    self.assertEquals (rev, 78)
    self.assertEquals (qualifier, 'snapshot')
    self.assertEquals (build, 0)

    (major, minor, rev, qualifier, build) = vercmp.getCanonical ('44.33.22-ReLeASe-9901')
    self.assertEquals (major, 44)
    self.assertEquals (minor, 33)
    self.assertEquals (rev, 22)
    self.assertEquals (qualifier, 'release')
    self.assertEquals (build, 9901)
    
    return

  def testCompare (self):
    self.assertEquals (vercmp.compare ('', ''), 0)
    self.assertEquals (vercmp.compare ('', '0.0'), 0)
    self.assertEquals (vercmp.compare ('', '0.0.0--0'), 0)
    self.assertTrue (vercmp.compare ('', '1') < 0)
    self.assertTrue (vercmp.compare ('1', '0') > 0)

    self.assertTrue (vercmp.compare ('1.3.2', '2.1.1') < 0)
    self.assertTrue (vercmp.compare ('1.3.2', '1.4.0') < 0)
    self.assertTrue (vercmp.compare ('1.3.2', '1.3.3') < 0)

    self.assertTrue (vercmp.compare ('2.1.1', '1.3.2') > 0)
    self.assertTrue (vercmp.compare ('1.4.0', '1.3.2') > 0)
    self.assertTrue (vercmp.compare ('1.3.3', '1.3.2') > 0)

    self.assertTrue (vercmp.compare ('1.3', '1.2]') > 0)
    return

  def testSatisfiesMinimum (self):
    self.assertFalse (vercmp.satisfies ("1.2", "1.3"))
    self.assertFalse (vercmp.satisfies ("12.1.2-a-0", "12.1.2-a-1"))
    self.assertTrue  (vercmp.satisfies ("1.3", "1.2"))
    self.assertTrue  (vercmp.satisfies ("12.1.2-2-0", "12.1.2-2-0"))
    self.assertTrue  (vercmp.satisfies ("1.2.3-RELEASE", "1.2.3-RELEASE"))

    self.assertFalse (vercmp.satisfies ("1.2", "[1.3,]"))
    self.assertFalse (vercmp.satisfies ("12.1.2-a-0", "[12.1.2-a-1,]"))
    self.assertFalse (vercmp.satisfies ("1.3", "[1.4,]"))
    self.assertTrue  (vercmp.satisfies ("1.3", "[1.2,]"))
    self.assertTrue  (vercmp.satisfies ("12.1.2-2-0", "[12.1.2-2-0,]"))
    self.assertTrue  (vercmp.satisfies ("1.2.3-RELEASE", "[1.2.3-RELEASE,]"))

    self.assertFalse (vercmp.satisfies ("1.2", "(1.3,)"))
    self.assertFalse (vercmp.satisfies ("12.1.2-a-0", "(12.1.2-a-1,)"))
    self.assertFalse (vercmp.satisfies ("1.3", "(1.4,)"))
    self.assertTrue  (vercmp.satisfies ("1.3", "(1.2,)"))
    self.assertFalse (vercmp.satisfies ("12.1.2-2-0", "(12.1.2-2-0,)"))
    self.assertFalse (vercmp.satisfies ("1.2.3-RELEASE", "(1.2.3-RELEASE,)"))
    return

  def testSatisfiesMaximum (self):
    self.assertTrue  (vercmp.satisfies ("1.2", "[,1.3]"))
    self.assertTrue  (vercmp.satisfies ("12.1.2-a-0", "[,12.1.2-a-1]"))
    self.assertFalse (vercmp.satisfies ("1.3", "[,1.2]"))
    self.assertTrue  (vercmp.satisfies ("1.3", "[,1.4]"))
    self.assertTrue  (vercmp.satisfies ("12.1.2-2-0", "[,12.1.2-2-0]"))
    self.assertTrue  (vercmp.satisfies ("1.2.3-RELEASE", "[,1.2.3-RELEASE]"))

    self.assertTrue  (vercmp.satisfies ("1.2", "(,1.3)"))
    self.assertTrue  (vercmp.satisfies ("12.1.2-a-0", "(,12.1.2-a-1)"))
    self.assertFalse (vercmp.satisfies ("1.3", "(,1.2)"))
    self.assertTrue  (vercmp.satisfies ("1.3", "(,1.4)"))
    self.assertFalse (vercmp.satisfies ("12.1.2-2-0", "(,12.1.2-2-0)"))
    self.assertFalse (vercmp.satisfies ("1.2.3-RELEASE", "(,1.2.3-RELEASE)"))
    return

  def testSatisfiesMinimumExclusive (self):
    # >=
    self.assertFalse (vercmp.satisfies ("1.2", "(1.3,)"))
    self.assertFalse (vercmp.satisfies ("12.1.2-a-0", "(12.1.2-a-1,)"))
    self.assertTrue  (vercmp.satisfies ("1.2.4.2", "(1.2,)"))
    self.assertFalse (vercmp.satisfies ("1.2", "(1.2,)"))
    self.assertFalse (vercmp.satisfies ("12.1.2-2-0", "(12.1.2-2-0,)"))
    self.assertFalse (vercmp.satisfies ("1.2.3-RELEASE", "(1.2.3-RELEASE,)"))
    return

  def testSatisfiesExact (self):
    self.assertFalse (vercmp.satisfies ("1.2", "[1.3]"))
    self.assertFalse (vercmp.satisfies ("12.1.2-a-0", "[12.1.2-a-1]"))
    self.assertFalse (vercmp.satisfies ("1.3", "[1.2]"))
    self.assertTrue  (vercmp.satisfies ("12.1.2-2-0", "[12.1.2-2-0]"))
    self.assertTrue  (vercmp.satisfies ("1.2.3-RELEASE", "[1.2.3-RELEASE]"))
    return

  def testSatisfiesRangeInclusive (self):
    self.assertTrue  (vercmp.satisfies ("1.1.4-asdf-23", "[1.1.4-asdf-23, 1.1.4-asdf-42]"))
    self.assertTrue  (vercmp.satisfies ("1.1.4-asdf-42", "(1.1.4-asdf-23, 1.1.4-asdf-42]"))

    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-22", "[1.1.4-asdf-23, 1.1.4-asdf-42]"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-43", "[1.1.4-asdf-23, 1.1.4-asdf-42]"))

    self.assertTrue  (vercmp.satisfies ("1.1.4-zzzz-22", "[1.1.4-asdf-23, 1.1.5-asdf-42]"))
    self.assertFalse (vercmp.satisfies ("1.1.4-aaaa-43", "[1.1.4-asdf-23, 1.1.5-asdf-42]"))
    
    self.assertFalse (vercmp.satisfies ("1.1.4-aaaa-23", "[1.1.4-asdf-23, 1.1.4-asdf-42]"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdg-23", "[1.1.4-asdf-23, 1.1.4-asdf-42]"))

    self.assertFalse (vercmp.satisfies ("1.1",   "[1.2,1.3]"))
    self.assertTrue  (vercmp.satisfies ("1.2",   "[1.2,1.3]"))
    self.assertTrue  (vercmp.satisfies ("1.2.5", "[1.2,1.3]"))
    self.assertTrue  (vercmp.satisfies ("1.3",   "[1.2,1.3]"))
    self.assertFalse (vercmp.satisfies ("1.4",   "[1.2,1.3]"))
    return

  def testSatisfiesRangeExclusiveStart (self):
    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-23", "(1.1.4-asdf-23, 1.1.4-asdf-42]"))
    self.assertTrue  (vercmp.satisfies ("1.1.4-asdf-42", "(1.1.4-asdf-23, 1.1.4-asdf-42]"))

    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-22", "(1.1.4-asdf-23, 1.1.4-asdf-42]"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-43", "(1.1.4-asdf-23, 1.1.4-asdf-42]"))

    self.assertTrue  (vercmp.satisfies ("1.1.4-zzzz-22", "(1.1.4-asdf-23, 1.1.5-asdf-42]"))
    self.assertFalse (vercmp.satisfies ("1.1.4-aaaa-43", "(1.1.4-asdf-23, 1.1.5-asdf-42]"))
    
    self.assertFalse (vercmp.satisfies ("1.1.4-aaaa-23", "(1.1.4-asdf-23, 1.1.4-asdf-42]"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdg-23", "(1.1.4-asdf-23, 1.1.4-asdf-42]"))

    self.assertFalse (vercmp.satisfies ("1.1",   "(1.2,1.3]"))
    self.assertFalse (vercmp.satisfies ("1.2",   "(1.2,1.3]"))
    self.assertTrue  (vercmp.satisfies ("1.2.5", "(1.2,1.3]"))
    self.assertTrue  (vercmp.satisfies ("1.3",   "(1.2,1.3]"))
    self.assertFalse (vercmp.satisfies ("1.4",   "(1.2,1.3]"))
    return

  def testSatisfiesRangeExclusiveEnd (self):
    self.assertTrue  (vercmp.satisfies ("1.1.4-asdf-23", "[1.1.4-asdf-23, 1.1.4-asdf-42)"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-42", "[1.1.4-asdf-23, 1.1.4-asdf-42)"))

    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-22", "[1.1.4-asdf-23, 1.1.4-asdf-42)"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-43", "[1.1.4-asdf-23, 1.1.4-asdf-42)"))

    self.assertTrue  (vercmp.satisfies ("1.1.4-zzzz-22", "[1.1.4-asdf-23, 1.1.5-asdf-42)"))
    self.assertFalse (vercmp.satisfies ("1.1.4-aaaa-43", "[1.1.4-asdf-23, 1.1.5-asdf-42)"))
    
    self.assertFalse (vercmp.satisfies ("1.1.4-aaaa-23", "[1.1.4-asdf-23, 1.1.4-asdf-42)"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdg-23", "[1.1.4-asdf-23, 1.1.4-asdf-42)"))

    self.assertFalse (vercmp.satisfies ("1.1",   "[1.2,1.3)"))
    self.assertTrue  (vercmp.satisfies ("1.2",   "[1.2,1.3)"))
    self.assertTrue  (vercmp.satisfies ("1.2.5", "[1.2,1.3)"))
    self.assertFalse (vercmp.satisfies ("1.3",   "[1.2,1.3)"))
    self.assertFalse (vercmp.satisfies ("1.4",   "[1.2,1.3)"))
    return

  def testSatisfiesRangeExclusive (self):
    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-23", "(1.1.4-asdf-23, 1.1.4-asdf-42)"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-42", "(1.1.4-asdf-23, 1.1.4-asdf-42)"))

    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-22", "(1.1.4-asdf-23, 1.1.4-asdf-42)"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdf-43", "(1.1.4-asdf-23, 1.1.4-asdf-42)"))

    self.assertTrue  (vercmp.satisfies ("1.1.4-zzzz-22", "(1.1.4-asdf-23, 1.1.5-asdf-42)"))
    self.assertFalse (vercmp.satisfies ("1.1.4-aaaa-43", "(1.1.4-asdf-23, 1.1.5-asdf-42)"))
    
    self.assertFalse (vercmp.satisfies ("1.1.4-aaaa-23", "(1.1.4-asdf-23, 1.1.4-asdf-42)"))
    self.assertFalse (vercmp.satisfies ("1.1.4-asdg-23", "(1.1.4-asdf-23, 1.1.4-asdf-42)"))

    self.assertFalse (vercmp.satisfies ("1.1",   "(1.2,1.3)"))
    self.assertFalse (vercmp.satisfies ("1.2",   "(1.2,1.3)"))
    self.assertTrue  (vercmp.satisfies ("1.2.0-something.0",   "(1.2,1.3)"))
    self.assertTrue  (vercmp.satisfies ("1.2.5", "(1.2,1.3)"))
    self.assertFalse (vercmp.satisfies ("1.3",   "(1.2,1.3)"))
    self.assertFalse (vercmp.satisfies ("1.4",   "(1.2,1.3)"))
    return

  def testSatisfiesMultipleRanges (self):
    self.assertTrue  (vercmp.satisfies ("0.3", "(,1.0],[1.2,)"))
    self.assertTrue  (vercmp.satisfies ("1.0", "(,1.0],[1.2,)"))
    self.assertFalse (vercmp.satisfies ("1.1", "(,1.0],[1.2,)"))
    self.assertTrue  (vercmp.satisfies ("1.2", "(,1.0],[1.2,)"))
    self.assertTrue  (vercmp.satisfies ("8.2", "(,1.0],[1.2,)"))

    self.assertTrue  (vercmp.satisfies ("0.3", "(,1.0),(1.2,)"))
    self.assertFalse (vercmp.satisfies ("1.0", "(,1.0),(1.2,)"))
    self.assertFalse (vercmp.satisfies ("1.1", "(,1.0),(1.2,)"))
    self.assertFalse (vercmp.satisfies ("1.2", "(,1.0),(1.2,)"))
    self.assertTrue  (vercmp.satisfies ("8.2", "(,1.0),(1.2,)"))
    return
  
  def testSatisfiesWithSpaces (self):
    self.assertTrue  (vercmp.satisfies ("1.2", " ( , 1.3  ] "))
    self.assertTrue  (vercmp.satisfies ("1.3", "( ,1.3]"))
    self.assertFalse (vercmp.satisfies ("1.4", "( , 1.3]"))
    self.assertTrue  (vercmp.satisfies ("1.2", "(  ,  1.3.5]"))
    return
  
if __name__ == '__main__':
  unittest.main()
