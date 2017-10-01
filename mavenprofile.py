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
      jdkActivation = self.activation['jdk']

      # if a specific version is specified, it should match exactly (e.g: 1.8)
      if len(jdkActivation) == len(jdkActivation.strip('[](),')):
        return (properties['jdk'].lower().strip() == jdkActivation.lower().strip())

      # if a range is specified, then compare accordingly (e.g: [1.8,1.9] )
      return vercmp.satisfies (properties['jdk'], jdkActivation)

    # is it avaliable as a property?
    if ('property' in self.activation):
      name = self.activation.get('property', {}).get ('name', '')
      if name in properties:
        value = self.activation.get('property', {}).get ('value', '')
        if value is None:
          value = ''
        
        # NOTE: there are several scenarios in order to expand properties for
        #       comparison, the simplest is the one implemented
        if properties.get(name, '').strip() == value.strip():
          return True

    return False


