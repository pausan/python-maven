#/usr/bin/env python
# -*- coding: utf-8 -*- 
import os,sys
import unittest

sys.path.append (os.path.join (os.path.dirname (__file__), '..'))

from mavencoord import MavenCoord
from mavendeps import MavenDep, MavenDeps
import mavenparser 

class MavenParserTest (unittest.TestCase):

  def testDepsResolveExclusionsNoVersion (self):
    return # FIXME!
    """ Test that we can get dependencies without exclusions
    """
    depsA = MavenDeps('A:A')
    depsB = MavenDep ('B:B')
    depsC = MavenDep ('C:C')
    depsD = MavenDep ('D:D')
    depsE = MavenDep ('E:E')

    # A->B->C
    # |  |
    # |  +->D
    # |  |
    # |  +->E
    # |
    # +->C
    depsB.add (depsC)
    depsB.add (depsD)
    depsB.add (depsE)
    depsA.add (depsB)
    depsA.add (depsC)

    depsA.root.addCoordToExclude ('D:D')
    depsB.addCoordToExclude ('C:C')

    self.assertEquals (
      depsA.getFlattenCoordIds(),
      ['B:B:', 'C:C:', 'D:D:', 'E:E:', 'C:C:']
    )

    # C should be removed from the branch of A and B
    # D should be removed from the branch of B
    # 
    # A->B->E
    # |
    # +->C
    depsA.resolve()

    self.assertEquals (
      depsA.getFlattenCoordIds(),
      ['B:B:', 'E:E:', 'C:C:']
    )
    return 
  

  def testDepsResolveScopeConflict (self):
    """ Test that we can get dependencies without exclusions
    """
    depsA = MavenDeps('A:A:jar:1:compile')
    depsB = MavenDep ('B:B:jar:1:compile')
    depsC = MavenDep ('C:C:jar:1:compile')
    depsCT = MavenDep ('C:C:jar:1:test')
    depsD = MavenDep ('D:D:jar:1:compile')

    # A->B->C:compile
    # |     |
    # |     +->D:compile
    # |
    # +->C:test
    depsC.add (depsD)
    depsB.add (depsC)
    depsA.add (depsB)
    depsA.add (depsCT)

    self.assertEquals (
      depsA.getFlattenCoordFullIds(),
      ['B:B:jar:1:compile', 'C:C:jar:1:compile', 'D:D:jar:1:compile', 'C:C:jar:1:test']
    )

    # C:test should be the only one removed since A->B->C->D
    depsA.resolve(scope = 'compile')

    self.assertEquals (
      depsA.getFlattenCoordFullIds(),
      ['B:B:jar:1:compile', 'C:C:jar:1:compile', 'D:D:jar:1:compile']
    )
    return 

  def testDepsResolveScopeConflictInverse (self):
    """ Test that we can get dependencies without exclusions
    """
    depsA = MavenDeps('A:A:jar:1:compile')
    depsB = MavenDep ('B:B:jar:1:compile')
    depsC = MavenDep ('C:C:jar:1:compile')
    depsCT = MavenDep ('C:C:jar:1:test')
    depsD = MavenDep ('D:D:jar:1:compile')

    # A->B->C:test
    # |     |
    # |     +->D:compile
    # |
    # +->C:compile
    depsCT.add (depsD)
    depsB.add (depsCT)
    depsA.add (depsB)
    depsA.add (depsC)

    self.assertEquals (
      depsA.getFlattenCoordFullIds(),
      ['B:B:jar:1:compile', 'C:C:jar:1:test', 'D:D:jar:1:compile', 'C:C:jar:1:compile']
    )

    # C:test should be the only one removed since A->B->C->D
    depsA.resolve(scope = 'compile')

    self.assertEquals (
      depsA.getFlattenCoordFullIds(),
      ['B:B:jar:1:compile', 'C:C:jar:1:compile']
    )
    return 

if __name__ == '__main__':
  unittest.main()
