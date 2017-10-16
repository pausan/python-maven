#!/usr/bin/env python
# -*- coding: utf-8 -*- 

from mavencoord import MavenCoord

class MavenVersionDb:
  """ This class serves as a dependency database so we can lookup 
  versions of packages that have been registered already.
  """
  def __init__ (self):
    self._db = {}
    self._warnings = set()
    return

  def parseFile (self, depsfile):
    """ _depsfile_ is the path to a filename that will be read and processed
    in order to inject all dependencies.

    The format of the file is similar to the one produced by the following
    maven command:

      $  mvn dependency:tree -DoutputType=text -Doutput=deps.txt

      The only difference is that the very first line, which references the
    coord we are in, should be commented out with '#' character.
    """
    with open (depsfile, 'rt') as f:
      for line in f:
        line = line.strip()
        if line.startswith ('#') or (len(line) == 0):
          continue

        self.register (line.lstrip ('=|+- \\'))
        
    return True

  def register (self, coord):
    """ Register given coord in the database
    """
    if isinstance (coord, list):
      for m in coord:
        self.register (m)
      return

    m = MavenCoord (coord)

    myId = m.group + ':' + m.artifact
    if (myId in self._db) and (self._db[myId] != m.version):
      self.dependencyWarningOnce (m.id, self._db[myId])
      m.version = self._db[myId]
      return m

    self._db[myId] = m.version
    return m

  def findOrRegister (self, coord):
    normCoord = self.find (coord)
    if normCoord is None:
      return self.register (coord)
    return normCoord

  def find (self, coord):
    """ Finds a coordinate that matches given group and artifact
    """
    coord = MavenCoord (coord)
    coord.version = self.getVersionFor (coord.group, coord.artifact)
    if not coord.version:
      return None
    return coord

  def getVersionFor (self, group, artifact):
    """ Get default version for given group and artifact
    """
    return self._db.get (group + ':' + artifact, None)

  def hasVersionFor (self, group, artifact):
    return self._db.has (group + ':' + artifact)

  def dependencyWarningOnce (self, coord, existingVersion):
    """ Show a dependency warning once
    """
    if coord in self._warnings:
      return
    
    self._warnings.add (coord)

    print (
      "WARNING: Unhandled dependency conflict for %s (expecting version '%s')" % (
        coord,
        existingVersion
      )
    )