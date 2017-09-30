#/usr/bin/env python
# -*- coding: utf-8 -*- 
import copy
from mavencoord import MavenCoord

class MavenDep:
  """ Class to model a single dependency along its internal dependencies
  """
  def __init__ (self, coord, optional = False):
    self.coord = MavenCoord (coord)
    self.optional = optional
    self.deps = []
    self.exclusions = []
    return

  def add (self, dep, override = False):
    """ Add dependency
    """
    if not isinstance (dep, MavenDep):
      raise Exception ("Expecting a MavenDep when adding dependency: %s" % str(dep))

    if override:
      self.deps = [d for d in self.deps if d.coord.name != dep.coord.name]

    elif ([d for d in self.deps if d.coord.name == dep.coord.name]):
      raise Exception ("Conflicting versions while adding dependencies: %s" % str(dep.coord))

    self.deps.append (dep)
    return

  def find (self, coord):
    """ Find a dependency based on the coord
    """
    if self.coord.id == MavenCoord(coord).id:
      return self

    for dep in self.deps:
      result = dep.find (coord)
      if result:
        return result
    
    return None

  def expand (self, properties):
    """ Expand internal variables recursively
    """
    self.coord.expand (properties)
    for dep in self.deps:
      dep.expand (properties)
    return 

  def count (self):
    """ Returns the number of dependencies recursively, counting even if there
    are duplicates in children (and not ignoring anything). Optional items
    will be counted as well.
    """
    total = 1
    for dep in self.deps:
      total += dep.count()
    return total

  def addCoordToExclude (self, dep2ignore):
    """ Add a coordinate to ignore
    """
    self.exclusions.append (MavenCoord (dep2ignore))
    return

  def flatten (self, skipOptional = True):
    """ Returns a list of all children flattened. Please note that this method
    won't be removing duplicates.
    """
    flat = []
    for child in self.deps:
      if skipOptional and child.optional:
        continue

      flat.append (child)
      flat.extend (child.flatten())

    return flat

  def resolve (self, scope = None, skipOptional = True):
    """ Resolve dependencies by excluding all dependencies that should
    be taking into account the exclusion rules in the tree.

    NOTE: it modifies the current tree of dependencies
    """
    if scope is None:
      pass
    elif isinstance (scope, basestring):
      scope = set ([scope])
    else:
      scope = set (scope)

    self._resolve ({}, scope, skipOptional)
    return self

  def _resolve (self, itemsToExclude, scopeSet, skipOptional):
    """ Resolve dependencies by excluding items
    """
    self.coord.resolve()

    for exclusion in self.exclusions:
      itemsToExclude[exclusion.name] = exclusion

    itemsToExcludeNext = itemsToExclude.copy()
    for dep in self.deps:
      itemsToExcludeNext[dep.coord.name] = dep.coord

    newDeps = []
    for dep in self.deps:
      if scopeSet and (dep.coord.scope not in scopeSet):
        continue

      if skipOptional and dep.optional:
        continue

      if dep.coord.name in itemsToExclude:
        if dep.coord.isContained (itemsToExclude[dep.coord.name]):        
          continue

        # version conflict
        # print dep.coord.id, "vs", itemsToExclude[dep.coord.name].id
        continue

      # need to copy to don't infect siblings with exclusions from sons
      # of this dependency      
      dep._resolve (itemsToExcludeNext.copy(), scopeSet, skipOptional)
      
      newDeps.append (dep)

    self.deps = newDeps
    self.exclusions = []
    return 

  def updateVersionsAndScope (self, depManagement):
    assert isinstance (depManagement, MavenDep)

    for dep in depManagement.deps:
      if self.coord.name == dep.coord.name:
        if not self.coord.version:
          self.coord.version = dep.coord.version

        if self.coord.scope == MavenCoord.SCOPE_DEFAULT:
          self.coord.scope = dep.coord.scope

        self.exclusions.extend (dep.exclusions)
    
    for dep in self.deps:
      dep.updateVersionsAndScope (depManagement)
    return


  def __repr__ (self):
    s = [self.coord.id]

    for dep in self.deps:
      s.append ('  ' + repr(dep).replace ('\n', '\n  '))

    for dep in self.exclusions:
      s.append ('  <<< ' + dep.id)

    return '\n'.join (s)


class MavenDeps:
  """ Class to manage maven dependencies, which are formed by
  groupId, artifactId and version.

  This class manages dependencies as a tree of MavenDep
  """
  def __init__ (self, coord = None):
    """ Initializes the dependencies by using a root coordinate of the
    package that the dependencies are going to defined for
    """
    self.root = MavenDep (coord)
    return

  def getRoot (self):
    return self.root

  def count (self):
    """ Returns the number of dependencies recursively, counting even if there
    are duplicates.
    """
    # remove 1 to account for the root element
    return self.root.count() - 1

  def add (self, dep, override = False):
    """ Adds a maven dependency by either specifying a coordinate string, a 
    MavenCoord or a MavenDep.
    """
    self.root.add (dep, override)
    return

  def find (self, coord):
    """ Find a dependency based on the coord
    """
    return self.root.find (coord)

  def clone (self):
    """ Returns a clone of this object
    """
    return copy.deepcopy (self)

  def merge (self, mavenDepsObj):
    """ Merge given mavenDepsObj dependencies into this one
    """
    if not isinstance (mavenDepsObj, MavenDeps):
      raise Exception ("Expecting MavenDeps object")

    for obj in mavenDepsObj.root.deps:
      self.add (copy.deepcopy (obj), override = True)
    return

  def expand (self, properties):
    """ Expand internal variables
    """
    self.root.expand (properties)
    return 

  def resolve (self, scope = None, skipOptional = True):
    """ Resolve dependencies by excluding all dependencies that should
    be taking into account the exclusion rules in the tree.

    NOTE: it modifies the current tree of dependencies
    """
    self.root.resolve (scope, skipOptional)
    return self

  def updateVersionsAndScope (self, deps):
    if isinstance (deps, MavenDeps):
      self.root.updateVersionsAndScope (deps.root)
    else:
      self.root.updateVersionsAndScope (deps)
    return

  def getFlattenDeps (self, skipOptional = True):
    """ Returns a flatten list of all dependencies
    """
    return self.root.flatten (skipOptional)

  def getFlattenCoords (self, skipOptional = True):
    """ Returns a flatten list of all dependencies as coordinates
    """
    return [d.coord for d in self.root.flatten (skipOptional)]

  def getFlattenCoordIds (self, skipOptional = True):
    """ Returns a flatten list of all dependencies as coordinates
    """
    return [d.coord.id for d in self.root.flatten (skipOptional)]

  def __repr__ (self):
    return repr(self.root)