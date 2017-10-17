#/usr/bin/env python
# -*- coding: utf-8 -*- 

from mavencoord import MavenCoord
from maven import Maven
from mavenprofile import MavenProfile
from mavendeps import MavenDep, MavenDeps
import requests
import xmltodict
import json

def parse (string = None, file = None, url = None):
  """ Parse a string or a file or a url
  """
  if url is not None:
    parseUrl (url)
    
  elif file is not None:
    parseFile (file)

  elif string is not None:
    parseString (string)

  return None

def parseUrl (pomUrl):
  """ Parse a pom.xml URL and returns a Maven object or None
  """
  r = requests.get (pomUrl)
  if r.status_code != 200:
    return None

  return parseString (r.text)

def parseFile (pomFile):
  """ Parses a pom.xml file and returns a Maven object or None
  """
  with open (pomFile, 'rb') as f:
    return parseString (f.read())
  return None

def parseString (pomString):
  """ Parses a pom.xml string and returns a Maven object
  """
  maven = Maven()

  obj = xmltodict.parse (pomString)

  # get project as a dict
  project = obj.get ('project', {})

  maven.parent = _parseParent (project)

  # parse coord (taking into account inheritance)
  maven.coord = MavenCoord (project)
  if not maven.coord.group:
    maven.coord.group = maven.parent.group

  if not maven.coord.version:
    maven.coord.version = maven.parent.version

  maven.deps = _parseDependencies (project, maven.coord)
  maven.depsManagement = _parseDependencyManagement (project, maven.coord)  
  maven.properties = _parseProperties (project)
  maven.profiles = _parseProfiles (project, maven.coord)

  return maven

def _parseParent (projectObj):
  """ Parse parent coordinates
  """
  return MavenCoord (projectObj.get ('parent', {}))
   
def _parseDependencyManagement (project, rootCoord):
  """ Parse dependency management as if they were normal dependencies
  """
  return _parseDependencies (project.get ('dependencyManagement', {}), rootCoord)

def _parseDependencies (projectObj, rootCoord):
  """ Parse maven dependencies from project
  """
  deps = MavenDeps(rootCoord)

  # parse dependencies
  dependencies = projectObj.get ('dependencies', {})
  if dependencies is None:
    dependencies = []
  else:
    dependencies = dependencies.get ('dependency', [])

  if isinstance (dependencies, dict):
    dependencies = [ dependencies ]
  
  for depDict in dependencies:
    optional = (depDict.get ('optional', 'false').lower() == 'true')
    dep = MavenDep (depDict, optional = optional)
    deps.add (dep)

    exclusions = depDict.get ('exclusions', {})
    if exclusions is None:
      exclusions = []
    else:
      exclusions = exclusions.get ('exclusion', [])
      
    if isinstance (exclusions, dict):
      exclusions = [exclusions]

    for exclusion in exclusions:
      dep.addCoordToExclude (exclusion)

  return deps

def _parseProperties (projectObj):
  """ Parse maven properties
  """
  properties = {}
  
  allProperties = projectObj.get ('properties', {})
  if allProperties is None:
    allProperties = {}

  for k, v in allProperties.items():
    # when v is a list means that the same property is specified more
    # than once, on those scenarios just get the last one defined
    #
    # XML is like:
    #   <prop>myvalue1</prop>
    #   <prop>myvalue2</prop>
    #   
    # then v is like:
    #   v = ['myvalue1', 'myvalue2']
    if isinstance (v, list):
      v = v[-1]
    
    properties [k] = v if (v is not None) else ''

  return properties

def _parseProfiles (projectObj, mavenCoord):
  """ Parse maven profiles
  """
  allProfileObjs = projectObj.get ('profiles', {})
  if allProfileObjs is None:
    allProfileObjs = []
  else :
    allProfileObjs = allProfileObjs.get ('profile', [])

  if isinstance (allProfileObjs, dict):
    allProfileObjs = [ allProfileObjs ]

  profiles = []
  for profileObj in allProfileObjs:
    profile = MavenProfile()
    profile.activation = profileObj.get ('activation', {})
    profile.deps = _parseDependencies (profileObj, mavenCoord)
    profile.depsManagement = _parseDependencyManagement (profileObj, mavenCoord)  
    profile.properties = _parseProperties (profileObj)

    profiles.append (profile)

  return profiles
