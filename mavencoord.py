#/usr/bin/env python
# -*- coding: utf-8 -*- 
import mavenversioncmp as vercmp

class MavenCoord:
  """ This class helps to manage maven coordinates, which are formed by
  groupId, artifactId and version.

  This class considers _name_ to the string composed as 'groupId:artifact'
  """
  SCOPE_DEFAULT = 'default'
  SCOPE_COMPILE = 'compile'

  def __init__ (self, coordObject = None):
    self.group    = ''
    self.artifact = ''
    self.version  = ''
    self.type     = 'jar'
    self.scope    = MavenCoord.SCOPE_DEFAULT

    if coordObject is None:
      return

    elif isinstance (coordObject, MavenCoord):
      self.copy (coordObject)
      return

    elif isinstance (coordObject, basestring):
      self._initFromString (coordObject)
      return

    elif isinstance (coordObject, dict):
      self._initFromDict (coordObject)
      return
    return

  @property
  def name (self):
    """ Returns both the group and the artifact ids as a string
    separated by colon
    """
    return '%s:%s' % (self.group, self.artifact)

  @property
  def id (self):
    """ Returns the group, artifact and version as a colon-separated
    string
    """
    return '%s:%s:%s' % (self.group, self.artifact, self.version)
  
  @property
  def full (self):
    """ Returns the full maven coordinate
    """
    return '%s:%s:%s:%s:%s' % (
      self.group,
      self.artifact,
      self.type,
      self.version,
      self.scope
    )

  def resolve (self):
    self.scope = MavenCoord.resolveScope (self.scope)
    return

  def empty(self):
    """ Returns True when group or artifact are not defined
    """
    if (self.group and self.artifact):
      return False
    return True

  def expand (self, properties):
    """ Expand variables found in the properties
    """
    for k, v in properties.items():
      self.group = self.group.replace ('${%s}' % k, v)
      self.artifact = self.artifact.replace ('${%s}' % k, v)
      self.version = self.version.replace ('${%s}' % k, v)
    return

  def _initFromString (self, coordString):
    """ Initialize coordinate from string, such as

      >>> _initFromString ("group:artifact:version")
      >>> _initFromString ("group:artifact:type:version")
      >>> _initFromString ("group:artifact:type:version:scope")
    """
    splitCoord = coordString.split (':')
    if len(splitCoord) == 1:
      splitCoord.append (splitCoord[0]) # artifact = group 

    # group:artifact:type:version:scope
    if len(splitCoord) == 5:
      splitCoord.pop(2) # remove type

    self.group    = splitCoord[0]
    self.artifact = splitCoord[1]
    self.version  = splitCoord[2] if (len(splitCoord) > 2) else ''
    self.scope    = splitCoord[3] if (len(splitCoord) > 3) else MavenCoord.SCOPE_DEFAULT
    return

  def _initFromDict (self, coordDict):
    self.group    = coordDict.get ('groupId', '')
    self.artifact = coordDict.get ('artifactId', '')
    self.version  = coordDict.get ('version', '')
    self.scope    = coordDict.get ('scope', MavenCoord.SCOPE_DEFAULT)
    return

  @staticmethod
  def create (group, artifact, version = None, scope = SCOPE_DEFAULT):
    return MavenCoord('%s:%s:%s:%s' % (
      group,
      artifact,
      '' if (version is None) else version,
      scope
    ))

  def clone (self):
    """ Copy data from another maven module object
    """
    new = MavenCoord()
    new.group    = self.group
    new.artifact = self.artifact
    new.version  = self.version
    new.scope    = self.scope
    return new

  def isContainedIn (self, listOfCoords):
    """ Returns True if the current coord is contained in any of the coords 
    contained in the passed list
    """
    for coord in listOfCoords:
      if self.isContained (coord):
        return True
    return False

  def isContained (self, coord):
    """ 

    Example:
      >>> MavenCoord('A:B').isContained ('A:B')
      True
      >>> MavenCoord('A:B:1.0').isContained ('A:B')
      True
      >>> MavenCoord('A:B:1.2').isContained ('A:B:1.0')
      False
    """
    if isinstance (coord, basestring):
      coord = MavenCoord(coord)

    if (
      (self.id.strip(':') == coord.id.strip(':')) or
      (self.name == coord.id.strip(':'))
    ):
      return True

    # TODO: check versioning in coord

    return False

  def copy (self, obj):
    """ Copy data from another maven module object
    """
    self.group    = obj.group
    self.artifact = obj.artifact
    self.version  = obj.version
    self.scope    = obj.scope
    return self

  def __str__ (self):
    return self.id

  def __repr__ (self):
    return self.full


  @staticmethod
  def resolveScope (scope):
    """ Resolves the scope to a canonical value (default is converted to compile)
    """
    if scope == MavenCoord.SCOPE_DEFAULT:
      return MavenCoord.SCOPE_COMPILE
    return scope

  @staticmethod
  def resolveConflict (coord1, coord2):
    """ Resolve given coordinate conflict by sticking with the highest
    version that resolves the conflict.

    Returns the coordinate object with the highest version that resolves
    the conflict.

    It raises an exception if it cannot resolve the conflict
    """
    cmpValue = vercmp.compare (coord1.id, coord2.id)
    newScope = MavenCoord.resolveScopeConflict (coord1.scope, coord2.scope)

    # same value? any of both will do
    if cmpValue == 0:
      c1scope = MavenCoord.resolveScope (coord1.scope)
      c2scope = MavenCoord.resolveScope (coord2.scope)
      if c1scope != c2scope:
        if c1scope == newScope:
          return coord1
        else:
          return coord2

      return coord1

    # coord1 > coord2
    if cmpValue > 0:
      if vercmp.satisfies (coord1, coord2):
        return coord1

    # coord2 > coord1 or coord1 is higher and does not satisfies coord2
    if vercmp.satisfies (coord2, coord1):
      return coord2

    raise Exception (
      "Could not resolve conflict! '%s' vs '%s'" % (coord1.id, coord2.id)
    )

  @staticmethod
  def resolveScopeConflict (scope1, scope2):
    scope1 = MavenCoord.resolveScope (scope1)
    scope2 = MavenCoord.resolveScope (scope2)

    return {
      'compile' : {
        'compile' : 'compile',
        'provided' : 'compile',
        'runtime' : 'compile',
        'system' : 'compile',
        'test' : 'compile',
      },
      'provided' : {
        'compile' : 'compile',
        'provided' : 'provided',
        'runtime' : 'runtime',
        'system' : 'provided',
        'test' : 'provided',
      },
      'runtime' : {
        'compile' : 'compile',
        'provided' : 'runtime',
        'runtime' : 'runtime',
        'system' : 'runtime',
        'test' : 'runtime',
      },
      'system' : {
        'compile' : 'compile',
        'provided' : 'system',
        'runtime' : 'system',
        'system' : 'system',
        'test' : 'system',
      },
      'test' : {
        'compile' : 'compile',
        'provided' : 'test',
        'runtime' : 'runtime',
        'system' : 'test',
        'test' : 'test'
      },
    }[scope1][scope2]
