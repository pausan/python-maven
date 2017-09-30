#/usr/bin/env python
# -*- coding: utf-8 -*- 
from mavencoord import MavenCoord
from mavendeps import MavenDeps
import mavenversioncmp as vercmp

class MavenProfile:
  """ Represents a partial view of a single maven profile
  """
  def __init__ (self):
    self.activation = {}
    self.deps = MavenDeps ()
    self.depsManagement = MavenDeps ()
    self.properties = {}
    
    # TODO: self.resources
    # TODO: self.testResources
    return

  def isActive (self, properties = {}):
    if self.activation.get ('activeByDefault', 'false').lower() == 'true':
      return True
    
    if ('jdk' in self.activation) and ('jdk' in properties):
      return vercmp.satisfies (properties['jdk'], self.activation['jdk'])

    # is it avaliable as a property?
    if ('property' in self.activation):
      name = self.activation.get('property', {}).get ('name', '')
      value = self.activation.get('property', {}).get ('value', '')
      
      # NOTE: there are several scenarios in order to expand properties for
      #       comparison, the simplest is the one implemented
      if properties.get(name, '').strip() == value.strip():
        return True

    return False


