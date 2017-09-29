#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import os,sys
import unittest

sys.path.append (os.path.join (os.path.dirname (__file__), '..'))

from mavencoord import MavenCoord

class MavenCoordTest (unittest.TestCase):

  def testInitFromString (self):
    m = MavenCoord ('')
    self.assertTrue (m.empty())
    self.assertTrue (m.group == '')
    self.assertTrue (m.artifact == '')
    self.assertTrue (m.version == '')
    self.assertTrue (m.scope == MavenCoord.SCOPE_DEFAULT)

    m = MavenCoord ('junit')
    self.assertFalse (m.empty())
    self.assertTrue (m.group == 'junit')
    self.assertTrue (m.artifact == 'junit')
    self.assertTrue (m.version == '')
    self.assertTrue (m.scope == MavenCoord.SCOPE_DEFAULT)

    m = MavenCoord ('g:a:v')
    self.assertTrue (m.group == 'g')
    self.assertTrue (m.artifact == 'a')
    self.assertTrue (m.version == 'v')
    self.assertTrue (m.scope == MavenCoord.SCOPE_DEFAULT)

    m = MavenCoord ('g:a:v:s')
    self.assertTrue (m.group == 'g')
    self.assertTrue (m.artifact == 'a')
    self.assertTrue (m.version == 'v')
    self.assertTrue (m.scope == 's')

    m = MavenCoord ('g:a:t:v:s')
    self.assertTrue (m.group == 'g')
    self.assertTrue (m.artifact == 'a')
    self.assertTrue (m.version == 'v')
    self.assertTrue (m.scope == 's')
    return

  def testResolve (self):
    m = MavenCoord ('')
    m.resolve()
    self.assertTrue (m.empty())
    self.assertTrue (m.group == '')
    self.assertTrue (m.artifact == '')
    self.assertTrue (m.version == '')
    self.assertTrue (m.scope == 'compile')
    return

  def testInitFromDict (self):
    m = MavenCoord ({})
    self.assertTrue (m.group == '')
    self.assertTrue (m.artifact == '')
    self.assertTrue (m.version == '')
    self.assertTrue (m.scope == MavenCoord.SCOPE_DEFAULT)

    m = MavenCoord ({
      'groupId' : 'g',
      'artifactId' : 'a',
    })
    self.assertTrue (m.group == 'g')
    self.assertTrue (m.artifact == 'a')
    self.assertTrue (m.version == '')
    self.assertTrue (m.scope == MavenCoord.SCOPE_DEFAULT)

    m = MavenCoord ({
      'groupId' : 'g',
      'artifactId' : 'a',
      'version' : 'v',
      'scope' : 's'
    })
    self.assertTrue (m.group == 'g')
    self.assertTrue (m.artifact == 'a')
    self.assertTrue (m.version == 'v')
    self.assertTrue (m.scope == 's')
    return

  def testInitFromObj (self):
    m = MavenCoord (MavenCoord('g:a:v:s'))
    self.assertTrue (m.group == 'g')
    self.assertTrue (m.artifact == 'a')
    self.assertTrue (m.version == 'v')
    self.assertTrue (m.scope == 's')

  def testClone (self):
    m = MavenCoord ('g:a:v:s')
    a = m.clone()
    self.assertTrue (a.group == 'g')
    self.assertTrue (a.artifact == 'a')
    self.assertTrue (a.version == 'v')
    self.assertTrue (a.scope == 's')

  def testName (self):
    ga1 = MavenCoord ('g:a:1.0')
    ga2 = MavenCoord ('g:a:2.0')
    gb1 = MavenCoord ('g:b:1.0')
    ca1 = MavenCoord ('c:a:1.0')

    self.assertEquals (ga1.name,  ga1.name)
    self.assertEquals (ga1.name,  ga2.name)
    self.assertNotEquals (ga1.name,  gb1.name)
    self.assertNotEquals (ga1.name,  ca1.name)
    return

  def testIsContained (self):
    self.assertTrue (MavenCoord('A:B').isContained ('A:B'))
    self.assertTrue (MavenCoord('A:B:1.0').isContained ('A:B'))
    self.assertFalse (MavenCoord('A:B:1.2').isContained ('A:B:1.0'))
    return
