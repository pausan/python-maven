#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import os
import re
import requests
import shutil
import xmltodict

from maven import Maven
from mavencoord import MavenCoord
from mavenversiondb import MavenVersionDb
import mavenversioncmp as mavenvercmp
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
    self._jdkVersion = Maven.DEFAULT_JDK_VERSION

    if isinstance (versionDb, basestring):
      self._versionDb = MavenVersionDb()
      self._versionDb.parseFile (versionDb)

    elif isinstance (versionDb, MavenVersionDb):
      self._versionDb = versionDb

    # prepare cache dir
    if self._cacheDir and (not os.path.exists (self._cacheDir)):
      os.makedirs (self._cacheDir)

    return

  def setJdkVersion (self, jdkVersion):
    """ This version is used when resolving all maven objects. The value
    specified here will be used by default when downloading items from
    given repository.
    """
    self._jdkVersion = jdkVersion
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

  def getBaseUrlFor (self, coord):
    coord = MavenCoord (coord)
    baseurl = "%(group)s/%(artifact)s/%(version)s/%(artifact)s-%(version)s" % {
      'group'    : '/'.join (coord.group.split('.')),
      'artifact' : coord.artifact,
      'version'  : coord.version
    }      
    return self._repoUrl.rstrip('/') + '/' + baseurl.lstrip('/')

  def getJarUrlFor (self, coord):
    """ Returns the URL for downloading the artifact for given coordinate
    """
    return self.getBaseUrlFor (coord) + '.jar'

  def getPomUrlFor (self, coord):
    """ Returns the URL for downloading given coordinate
    """
    return self.getBaseUrlFor (coord) + '.pom'

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

    return self._fetchTreeDeps (
      coord,
      scope,
      downloadedItems = {},
      exclusions = {}
    )

  def downloadUrl (self, downloadUrl):
    """ Downloads given URL and saves the file in the cache dir, in case
    the file is already there, it won't download the file.

    Returns the path where the file is stored.
    """
    jarFileName = downloadUrl.split('/')[-1]
    destJarPath = os.path.join (self._cacheDir, jarFileName)

    if os.path.exists (destJarPath):
      return destJarPath

    r = requests.get(downloadUrl, stream=True)
    with open(destJarPath, 'wb') as f:
        shutil.copyfileobj(r.raw, f)

    return destJarPath    

  def downloadArtifacts (self, coord, scope):
    """ Resolves all dependencies for given coord and downloads all artifacts
    """
    if isinstance(coord, list):
      result = []
      for c in coord:
        result.extend (self.downloadArtifacts (c, scope))
      return result

    mavenObj = self.fetchResolvedTree (coord, scope)
    if not mavenObj:
      return []

    result = []
    for coord in [MavenCoord(coord)] + mavenObj.deps.getFlattenCoords():
      normCoord = self._versionDb.findOrRegister (coord)
      if normCoord.version and coord.version:
        if mavenvercmp.compare (coord.version, normCoord.version) > 0:
          print (
            "WARNING: it seems you are downloading an outdated version (update your version DB):\n"
            "  - proposal: %s\n" 
            "  -    using: %s" % (coord, normCoord)
          )

      downloadUrl = self.getJarUrlFor (normCoord)
      destJarPath = self.downloadUrl (downloadUrl)
      result.append (destJarPath)
    return result

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
        if mavenvercmp.compare (
          downloadedItems [coord.name].coord.id,
          coord.id
        ) < 0:
          # TODO: adjust versions versions
          print "WARNING: expecting same coord id for package '%s' vs '%s'" % (coord.id, downloadedItems [coord.name].coord.id)
      return downloadedItems [coord.name]

    maven = self.fetchWithAncestors (coord)
    if not maven:
      return None

    maven.resolve (jdkVersion = self._jdkVersion)

    # TODO: handle provided

    children = {}
    for dep in maven.deps.getFlattenDeps(skipOptional = True):
      if (dep.coord.scope != scope):
        continue

      if dep.coord.name in exclusions:
        if dep.coord.isContained (exclusions [dep.coord.name]):
          # exclude dep
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
      mavenChild.resolve (jdkVersion = self._jdkVersion)

      children [dep.coord.id] = mavenChild

    # update dependencies of this element
    for dep in maven.deps.root.deps:
      if dep.coord.id not in children:
        continue

      # assert dep.coord.id == mavenChild.deps.root.coord.id
      childDepsClone = children[dep.coord.id].deps.clone()
      dep.deps += childDepsClone.root.deps
      dep.exclusions += childDepsClone.root.exclusions

    downloadedItems [coord.name] = maven

    maven.resolve (scope = scope, jdkVersion = self._jdkVersion)
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
    """ Saves data to cache
    """
    cacheFile = self._cacheFile (cacheName)
    with open (cacheFile, 'wb') as f:
      f.write (data.encode('utf-8'))
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
