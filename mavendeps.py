#/usr/bin/env python
# -*- coding: utf-8 -*- 
import copy
from collections import OrderedDict
from mavencoord import MavenCoord
import mavenversioncmp as vercmp

class MavenDep:
  """ Class to model a single dependency along its internal dependencies
  """
  def __init__ (self, coord, optional = False):
    self.coord = MavenCoord (coord)
    self.optional = optional
    self.deps = []
    self.exclusions = []
    return

  def add (self, dep):
    """ Add a new dependency

    NOTE: multiple dependencies to the same coord can be added, if that happens
    they will be resolved at the end by following some prioritization rules.
    """
    if not isinstance (dep, MavenDep):
      raise Exception ("Expecting a MavenDep when adding dependency: %s" % str(dep))

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

    self._removeOptionalAndExclusionsInTree ({}, scope, skipOptional)

    # resolve modules included more than once with different versions
    winnerCoordFullIds = self._findWinnerCoordsInTree ()
    self._removeNonWinnerDepsInTree (winnerCoordFullIds)

    self._removeDuplicatesInTree ( set() )
    return self

  def _removeDuplicatesInTree (self, itemsAdded):
    newDeps = OrderedDict()
    for dep in self.deps:
      # don't add same item twice when resolving a tree
      if dep.coord.full in itemsAdded:
        continue

      newDeps[dep.coord.name] = dep
      itemsAdded.add (dep.coord.full)

    for dep in newDeps.values():
      dep._removeDuplicatesInTree (itemsAdded)

    self.deps = newDeps.values()
    return

  def _removeOptionalAndExclusionsInTree (self, itemsToExclude, scopeSet, skipOptional):
    self.coord.resolve()

    for exclusion in self.exclusions:
      itemsToExclude[exclusion.name] = exclusion

    newDeps = OrderedDict()
    for dep in self.deps:
      if scopeSet and (dep.coord.scope not in scopeSet):
        continue

      if skipOptional and dep.optional:
        continue

      if dep.coord.name in itemsToExclude:
        if dep.coord.isContained (itemsToExclude[dep.coord.name]):        
          continue

        # excusion pseudo-match?
        # print dep.coord.id, "vs", itemsToExclude[dep.coord.name].id
        continue

      if dep.coord.name in newDeps:
        dep = MavenDep.resolveDependencyConflict (dep, newDeps[dep.coord.name])

      newDeps[dep.coord.name] = dep

    # resolve children
    for dep in newDeps.values():
      # need to copy to not modify siblings with exclusions from sons
      # of this dependency      
      dep._removeOptionalAndExclusionsInTree (itemsToExclude.copy(), scopeSet, skipOptional)
      
    self.deps = newDeps.values()
    self.exclusions = []
    return 

  def _removeNonWinnerDepsInTree (self, winnerCoordFullIds):
    """ Remove all duplicates which have not
    """
    newDeps = []
    for dep in self.deps:
      if dep.coord.full in winnerCoordFullIds:
        dep._removeNonWinnerDepsInTree (winnerCoordFullIds)
        newDeps.append (dep)

    self.deps = newDeps
    return

  def _findWinnerCoordsInTree (self):
    """ Finds which coordinates with duplicates are the ones that should
    stay in the tree.

    Returns a set of strings with the full coordinates of the 
    """
    allCoords = [x.coord for x in self.flatten (skipOptional = False)]

    winnerCoords = {}
    for coord in allCoords:
      if coord.name in winnerCoords:
        winnerCoord = MavenCoord.resolveConflict (coord, winnerCoords[coord.name])
        if winnerCoord.full != coord.full:
          continue

      winnerCoords[coord.name] = coord

    return set([c.full for c in winnerCoords.values()])


  def _resolve (self, itemsToExclude, itemsAdded, scopeSet, skipOptional):
    """ Resolve dependencies by excluding items and selecting the proper
    version in case there are "duplicates" for the same coord.name
    """
    self.coord.resolve()

    for exclusion in self.exclusions:
      itemsToExclude[exclusion.name] = exclusion

    newDeps = OrderedDict()
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

      if dep.coord.name in newDeps:
        dep = MavenDep.resolveDependencyConflict (dep, newDeps[dep.coord.name])

      # don't add same item twice when resolving a tree
      if dep.coord.full in itemsAdded:
        continue

      newDeps[dep.coord.name] = dep
      itemsAdded.add (dep.coord.full)

    # resolve children
    for dep in newDeps.values():
      # need to copy to not modify siblings with exclusions from sons
      # of this dependency      
      dep._resolve (itemsToExclude.copy(), itemsAdded, scopeSet, skipOptional)
      
    self.deps = newDeps.values()
    self.exclusions = []
    return 

  @staticmethod
  def resolveDependencyConflict (dep1, dep2):
    """ Resolve given dependency conflict by sticking with the highest
    version that resolves the conflict.

    Returns the dependency object with the highest version that resolves
    the conflict.

    It raises an exception if it cannot resolve the conflict
    """
    cmpValue = vercmp.compare (dep1.coord.id, dep2.coord.id)
    newScope = MavenCoord.resolveScopeConflict (dep1.coord.scope, dep2.coord.scope)

    # same value? any of both will do
    if cmpValue == 0:
      dep1.coord.scope = newScope
      return dep1

    # dep1 > dep2
    if cmpValue > 0:
      if vercmp.satisfies (dep1.coord, dep2.coord):
        dep1.coord.scope = newScope
        return dep1

    # dep2 > dep1 or dep1 is higher and does not satisfies dep2
    if vercmp.satisfies (dep2.coord, dep1.coord):
      dep2.coord.scope = newScope
      return dep2

    raise Exception (
      "Could not resolve conflict! '%s' vs '%s'" % (dep1.coord.id, dep2.coord.id)
    )
  
  def updateVersionsAndScope (self, depManagement):
    """ Update default or missing version numbers and default or missing
    scopes with the right values inherited from given depManagement
    """
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
    s = [self.coord.full]

    for dep in self.deps:
      s.append ('  ' + repr(dep).replace ('\n', '\n  '))

    for dep in self.exclusions:
      s.append ('  <<< ' + dep.full)

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

  def add (self, dep):
    """ Adds a maven dependency by either specifying a coordinate string, a 
    MavenCoord or a MavenDep.
    """
    self.root.add (dep)
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
      self.add (copy.deepcopy (obj))
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
  
  def getFlattenCoordFullIds (self, skipOptional = True):
    """ Returns a flatten list of all dependencies as coordinates
    """
    return [d.coord.full for d in self.root.flatten (skipOptional)]

  def __repr__ (self):
    return repr(self.root)