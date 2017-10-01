#/usr/bin/env python
# -*- coding: utf-8 -*- 

from mavencoord import MavenCoord
from mavendeps import MavenDeps
import copy

class Maven:
  """ Maven object that represents a maven file with or without resolved
  dependencies (depends on how you create the Maven).

  You can use MavenRepo in order to download the whole maven file with
  all dependencies, or mavenparser to just parse a single file.
  """
  DEFAULT_JDK_VERSION = '1.9'

  def __init__ (self):
    self.location = None
    self.coord = MavenCoord ()
    self.parent = MavenCoord ()
    self.deps = MavenDeps ()
    self.depsManagement = MavenDeps ()
    self.properties = { 'jdk' : Maven.DEFAULT_JDK_VERSION }
    self.profiles = []

    # TODO: self.resources
    # TODO: self.testResources

    return

  def merge (self, mavenObj):
    self.deps.merge (mavenObj.deps)
    self.depsManagement.merge (mavenObj.depsManagement)
    self.properties.update (mavenObj.properties)
    self.profiles.extend (mavenObj.profiles)
    return

  def clone (self):
    """ Returns a clone of this object
    """
    return copy.deepcopy (self)

  def setProperty (self, name, value):
    self.properties[name] = value
    return

  def resolve (self, scope = None, skipOptional = True, jdkVersion = None):
    """ Resolve all dependencies and exclude whatever needs to be excluded.

    Resolving a maven object implies have all properties expanded as well.
    """
    if jdkVersion:
      self.properties['jdk'] = jdkVersion

    self._resolveProfiles ()

    self.expand ()

    self.deps.updateVersionsAndScope (self.depsManagement.root)
    self.deps.resolve (scope, skipOptional)
    return

  def _resolveProfiles (self):
    """ Resolves active profiles and updates current maven object with the
    new or modified dependencies and properties.
    """
    for profile in self.profiles:
      if not profile.isActive (self.properties):
        continue

      # when active merge all deps
      self.deps.merge (profile.deps)
      self.depsManagement.merge (profile.depsManagement)
      self.properties.update (profile.properties)

    self.profiles = []
    return

  def expand (self):
    """ Expands all property variables and gets the effective dependencies
    by modifying the current object.
    """
    self.properties['project.groupId'] = self.coord.group
    self.properties['project.artifactId'] = self.coord.artifact
    self.properties['project.version'] = self.coord.version

    self._expandProperties ()
    
    # expand dependencies
    self.deps.expand (self.properties)
    self.depsManagement.expand (self.properties)

    return

  def _expandProperties (self):
    """ Replaces the values of the properties that have properties embedded
    so that all properties end up without having ${symbol}.
    """
    numReplacements = 1
    while numReplacements > 0:
      numReplacements = 0

      # update properties with other properties
      updatedProperties = {}
      for k, v in self.properties.items():
        if v.find ('${') >= 0:
          nv = v
          
          for kk, vv in self.properties.items():
            nv = nv.replace ('${%s}' % kk, vv)
          
          numReplacements += (0 if (nv == v) else 1)
          v = nv
        
        updatedProperties[k] = v
      self.properties = updatedProperties

    return

  def __repr__ (self):
    s = ['%s (parent=%s)' % (self.coord.id, self.parent.id)]
    s.append ('deps:')
    s.append (repr(self.deps))
    s.append ('properties:')
    for k,v in self.properties.items():
      s.append ('  %s = %s' % (k, v))

    return '\n'.join (s)