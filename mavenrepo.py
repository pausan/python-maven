#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import os
import re
import requests
import shutil
import xmltodict

from mavencoord import MavenCoord
from mavenversiondb import MavenVersionDb
import mavenparser

class MavenRepo:
  """ Manages the dependencies and downloads of a maven repository
  """

  OFFICIAL_REPO_URL = 'https://repo.maven.apache.org/maven2/'

  def __init__ (
    self,
    url = OFFICIAL_REPO_URL,
    versionDb = None,
    cacheDir = '_maven-cache'
  ):
    self._cacheDir = cacheDir
    self._repoUrl = url
    self._versionDb = MavenVersionDb ()
    self._scheduledDownloads = {}

    if isinstance (versionDb, basestring):
      self._versionDb = MavenVersionDb()
      self._versionDb.parseFile (versionDb)

    elif isinstance (versionDb, MavenVersionDb):
      self._versionDb = versionDb

    # prepare cache dir
    if self._cacheDir and (not os.path.exists (self._cacheDir)):
      os.makedirs (self._cacheDir)

    return

  def cleanCache (self):
    """ Cleans the complete cache directory. Please keep in mind that this
    method is not thread safe.
    """
    if not os.path.exists (self._cacheDir):
      return

    shutil.rmtree (self._cacheDir)
    os.makedirs (self._cacheDir)
    return

  def getMetadataUrlFor (self, coord):
    """ Returns metadata URL to get information about a package
    """
    coord = MavenCoord (coord)
    baseurl = "%(group)s/%(artifact)s/maven-metadata.xml" % {
      'group'    : '/'.join (coord.group.split('.')),
      'artifact' : coord.artifact
    }      
    return self._repoUrl.rstrip('/') + '/' + baseurl.lstrip('/')

  def getPomUrlFor (self, coord):
    """ Returns the URL for downloading given coordinate
    """
    coord = MavenCoord (coord)
    baseurl = "%(group)s/%(artifact)s/%(version)s/%(artifact)s-%(version)s" % {
      'group'    : '/'.join (coord.group.split('.')),
      'artifact' : coord.artifact,
      'version'  : coord.version
    }      
    return self._repoUrl.rstrip('/') + '/' + baseurl.lstrip('/') + '.pom'

  def resolveCoord (self, coord):
    """ Resolve coordinate so it has group, artifact and version numbers

    Returns a valid MavenCoord object or None if it could not figure out
    a valid version.
    """
    coord = MavenCoord (coord)
    if coord.version:
      return coord
      
    newCoord = self._versionDb.find (coord)
    if newCoord:
      return newCoord

    # finally, let's download latest version from metadata file
    metadataUrl = self.getMetadataUrlFor (coord)
    metadataString = self._download2string (metadataUrl)
    if not metadataString:
      # raise Exception ("Cannot find out the coord version for: %s" % coord.id)
      return None

    obj = xmltodict.parse (metadataString)

    # get latest release version
    metadata = obj.get ('metadata', {})    
    versioning = metadata.get ('versioning', {})
    lastReleaseVersion = versioning.get ('release', None)

    if not lastReleaseVersion:
      return None

    coord.version = lastReleaseVersion
    return coord       

  def fetchOne (self, coord):
    """ Fetch maven file from coordinate
    """
    coord = self.resolveCoord (coord)
    if not coord:
      return None

    data = self._download2string (self.getPomUrlFor (coord))
    if data:
      return mavenparser.parseString (data)
    
    return None

  def fetchWithAncestors (self, coord):
    """ Fetch maven file from coordinate
    """
    maven = self.fetchOne (coord)
    if not maven:
      return None

    parentCoord = maven.parent
    while parentCoord and (not parentCoord.empty()):
      mavenParent = self.fetchOne (parentCoord)
      if (not mavenParent):
        break

      maven.merge (mavenParent)
      
      parentCoord = mavenParent.parent
   
    return maven

  def fetchResolvedTree (self, coord, scope):
    """ Recursively gets all the dependencies for given POM Coordinate
    """
    coord = self.resolveCoord (coord)
    if not coord:
      return None

    return self._fetchTreeDeps (coord, scope, {}, {})

  def _fetchTreeDeps (self, coord, scope, downloadedItems, exclusions):
    """ Downloads given coordinate and its dependencies recursively for given
    scope. All downloaded dependencies will be added to downloadedItems to avoid
    recursion.

    For quick lookups exclusions is mapping the coord.name with the actual
    coord excluded.
    """
    # is maven object in cache downloadedItems ['<group:artifact>']
    if coord.name in downloadedItems:
      if (downloadedItems [coord.name].coord.id != coord.id):
        print "WARNING: expecting same coord id for package '%s'" % coord.id
      return downloadedItems [coord.name]

    maven = self.fetchWithAncestors (coord)
    if not maven:
      return None

    maven.resolve()

    # TODO: handle provided
    # TODO: handle profiles

    children = {}
    for dep in maven.deps.getFlattenDeps(skipOptional = True):
      print "DEP: ", dep.coord.scope, dep.coord.id, dep.optional
      if (dep.coord.scope != scope):
        print "Skipping:", dep.coord.scope, dep.coord.name
        continue

      if dep.coord.name in exclusions:
        if dep.coord.isContained (exclusions [dep.coord.name]):
          print "Excluding:", dep.coord.scope, dep.coord.id
          continue

      # build the new exclusion list based on current dep
      newExclusions = exclusions.copy()
      for exclusion in dep.exclusions:
        newExclusions[exclusion.name] = exclusion

      # fetch child with deps
      mavenChild = self._fetchTreeDeps (
        dep.coord,
        scope,
        downloadedItems,
        newExclusions
      )
      mavenChild.resolve()

      children [dep.coord.id] = mavenChild

    # update dependencies
    for dep in maven.deps.root.deps:
      if dep.coord.id not in children:
        continue

      # assert dep.coord.id == mavenChild.deps.root.coord.id
      childDepsClone = children[dep.coord.id].deps.clone()
      dep.deps += childDepsClone.root.deps
      dep.exclusions += childDepsClone.root.exclusions

    maven.resolve()

    downloadedItems [coord.name] = maven

    return maven

  def _cacheFile (self, cacheName):
    if not self._cacheDir:
      return None

    cacheId = re.sub (r'[^a-z0-9_\.-]+', '_', cacheName, re.I | re.M | re.S) + '.cache'
    cacheFile = os.path.join (self._cacheDir, cacheId)
    return cacheFile

  def _cacheGet (self, cacheName, default = None):
    """ Returns data from the cache (if exists)
    """
    cacheFile = self._cacheFile (cacheName)
    if not cacheFile:
      return default

    if os.path.exists (cacheFile):
      with open (cacheFile, 'rb') as f:
        return f.read()

    return default

  def _cacheSave (self, cacheName, data):
    """ Returns data from the cache (if exists)
    """
    cacheFile = self._cacheFile (cacheName)
    with open (cacheFile, 'wb') as f:
      f.write (data)
    return

  def _download2string (self, url):
    data = self._cacheGet (url)
    if data:
      return data

    r = requests.get (url)
    if r.status_code != 200:
      return None

    self._cacheSave (url, r.text)
    return r.text
