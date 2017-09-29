#/usr/bin/env python
# -*- coding: utf-8 -*- 

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

  def resolve (self):
    if self.scope == MavenCoord.SCOPE_DEFAULT:
      self.scope = MavenCoord.SCOPE_COMPILE
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
