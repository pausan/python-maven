#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import os,sys
import unittest

sys.path.append (os.path.join (os.path.dirname (__file__), '..'))

from mavencoord import MavenCoord
from mavenversiondb import MavenVersionDb

class MavenVersionDbTest (unittest.TestCase):

  def testParseFile (self):
    verdb = MavenVersionDb()
    verdb.parseFile ('data/simple-deps.txt')

    self.assertEquals (verdb.find ('some-group:some-artifact'), None)

    self.assertEquals (
      verdb.find ('commons-beanutils:commons-beanutils').id,
      'commons-beanutils:commons-beanutils:1.8.3'
    )
    
    self.assertEquals (
      verdb.find ('commons-io:commons-io').id,
      'commons-io:commons-io:2.4'
    )
    
    self.assertEquals (
      verdb.find ('commons-lang:commons-lang').id,
      'commons-lang:commons-lang:2.6'
    )

    self.assertEquals (
      verdb.find ('javax.mail:mail').id,
      'javax.mail:mail:1.4.5'
    )
    
    self.assertEquals (
      verdb.find ('javax.servlet.jsp:jsp-api').id,
      'javax.servlet.jsp:jsp-api:2.2'
    )
    
    self.assertEquals (
      verdb.find ('javax.servlet:jstl').id,
      'javax.servlet:jstl:1.2'
    )
    
    self.assertEquals (
      verdb.find ('javax.servlet:javax.servlet-api').id,
      'javax.servlet:javax.servlet-api:3.0.1'
    )

    self.assertEquals (
      verdb.find ('javax.servlet:servlet-api').id,
      'javax.servlet:servlet-api:2.5'
    )
    return

  def testFind (self):
    verdb = MavenVersionDb()
    verdb.parseFile ('data/simple-deps.txt')

    self.assertEquals (
      verdb.find ('commons-beanutils:commons-beanutils').id,
      'commons-beanutils:commons-beanutils:1.8.3'
    )

    self.assertEquals (
      verdb.find ('commons-beanutils:commons-beanutils:').id,
      'commons-beanutils:commons-beanutils:1.8.3'
    )

    self.assertEquals (
      verdb.find ('commons-beanutils:commons-beanutils:1.8.3').id,
      'commons-beanutils:commons-beanutils:1.8.3'
    )

    self.assertEquals (
      verdb.find ('commons-beanutils:commons-beanutils:1.8.2').id,
      'commons-beanutils:commons-beanutils:1.8.3'
    )
    return
