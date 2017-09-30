#!/usr/bin/env python
# -*- coding: utf-8 -*- 
# 
# - 1.0           means x >= 1.0  (same as [1.0,])
# - (,1.0]        means x <= 1.0
# - (,1.0)        means x <  1.0
# - [1.0]         means x == 1.0
# - [1.0,]        means x >= 1.0
# - (1.0,)        means x > 1.0
# - (1.0,2.0)     means 1.0 < x < 2.0
# - [1.0,2.0]     means 1.0 <= x <= 2.0
# - [1.5,)        means x >= 1.5
# - (,1.0],[1.2,) means x <= 1.0 or x >= 1.2.
# - (,1.1),(1.1,) means x < 1.1 or x > 1.1  (excludes 1.1)
# 
# Default version comparison:
#   <major>.<minor>.<revision>([ -<qualififer> ] | [ -<build> ])
# 
# See:
#   https://cwiki.apache.org/confluence/display/MAVENOLD/Dependency+Mediation+and+Conflict+Resolution
#   https://maven.apache.org/enforcer/enforcer-rules/versionRanges.html
#
import re

_CANONICAL_REGEX = re.compile (r'''
  ^(?P<major>\d+)
   \.?
   (?P<minor>\d+)?
   \.?
   (?P<revision>\d+)?
   \-?
   (?P<qualifier>[^-]+)?
   \-?
   (?P<build>\d+)?
  $
  ''', 
  re.VERBOSE
)


def satisfies (version, versionConstraints):
  """ Checks if given version satisfies given version constraint that might
  include a version string or several ranges
  """
  return isContained (version, versionConstraints)

def isContained (version, versionConstraints):
  """ Checks if given version is contained in given version range

  """
  if not isinstance (versionConstraints, basestring):
    raise Exception ("Expecting version range to be a string")

  # split version by ranges
  versionRanges = [
    x.strip(',') for x in re.split (r'(.*[\)\]],)', versionConstraints) if x
  ]

  # if is contained in any range, then satisfies the rules
  for vr in versionRanges:
    if _isContained (version, vr):
      return True

  return False

def _isContained (version, versionRangeExpr):
  """ Compares version against given version range in order to see if
  it matches given criteria.
  """
  version = re.sub (r'\s+', '', version)
  versionRangeExpr = re.sub (r'\s+', '', versionRangeExpr)
  if version == versionRangeExpr:
    return True

  versionRanges = versionRangeExpr.split(',')
  if len(versionRanges) == 0:
    return False

  elif len(versionRanges) == 1:
    # has no braces/brackets, it means it is like '1.0' 
    # and should be normalized to '[1.0,]'
    if len(versionRanges[0]) == len(versionRanges[0].strip('[]()')):
      lowerBound = '[%s' % versionRanges[0]
      upperBound = ']'

    # has braces/brackets like '[1.2]', and will normalize to '[1.2,1.2]'
    else:
      lowerBound = '[%s' % versionRanges[0].strip('()[],')
      upperBound = '%s]' % versionRanges[0].strip('()[],')

    return _isContainedInBounds (version, lowerBound, upperBound)

  elif len(versionRanges) == 2:
    return _isContainedInBounds (
      version,
      lowerBound = versionRanges[0],
      upperBound = versionRanges[1]
    )

  else:
    raise Exception ("Version ranges expression not well formed: %s" % versionRangeExpr)

  return False

def _isContainedInBounds (version, lowerBound, upperBound):
  """ Checks if given version is contained in given bounds
  """
  # if lowerBound = '(' or '[' it passes the lower test since anything
  # is > or >= than minus infinite
  if (lowerBound != '(') and (lowerBound != '['):
    result = compare(version, lowerBound)

    # version should be > lower to continue
    if (lowerBound[0] == '(') and (result <= 0):
      return False

    # version should be >= lower to continue
    elif (lowerBound[0] == '[') and (result < 0):
      return False

  # if upperBound = ')' or ']' it passes the upper test since anything
  # is < or <= than infinite
  if (upperBound != ')') and (upperBound != ']'):
    result = compare(version, upperBound)

    # version should be less than my upper to continue
    if (upperBound[-1] == ')') and (result >= 0):
      return False

    # version should be less than or equal to upper value 
    # to continue, otherwise if it is greater we are done
    elif (upperBound[-1] == ']') and (result > 0):
      return False

  return True

def getCanonical (version):
  """ Returns the canonical representation of given version by returning a
  tuple containing (major, minor, revision, qualifier, build)

  Everything is a number apart of the qualifier.

  Example:
    >>> _getCanonical ("")
    (0, 0, 0, '', '')

    >>> _getCanonical ("1.3")
    (1, 3, 0, '', '')

    >>> _getCanonical ("1.3.9")
    (1, 3, 9, '', '')

    >>> _getCanonical ("1.3.9-SNAPSHOT-3")
    (1, 3, 9, 'SNAPSHOT', 3)
  """
  major = 0
  minor = 0
  revision = 0
  qualifier = ''
  build = 0

  m = _CANONICAL_REGEX.search (version.strip('[]()'))
  if m:
    m = m.groupdict()
    major     = int(m['major'])
    minor     = int(m['minor'] if m['minor'] else '0')
    revision  = int(m['revision'] if m['revision'] else '0')
    build     = int(m['build'] if m['build'] else '0')
    qualifier = (m['qualifier'].lower() if m['qualifier'] else '')

  return (major, minor, revision, qualifier, build)

def compare (a, b):
  """
  Compares two versions using the following rules:

  - numerical comparison of major version
  - numerical comparison of minor version
  - if revision does not exist, add ".0" for comparison purposes
  - numerical comparison of revision
  - if qualifier does not exist, it is newer than if it does
  - case-insensitive string comparison of qualifier
  - this ensures timestamps are correctly ordered, and SNAPSHOT is newer than an equivalent timestamp
  - this also ensures that beta comes after alpha, as does rc
  - if no qualifier, and build does not exist, add "-0" for comparison purposes
  - numerical comparison of build  
  """
  (aMajor, aMinor, aRevision, aQualifier, aBuild) = getCanonical(a)
  (bMajor, bMinor, bRevision, bQualifier, bBuild) = getCanonical(b)

  if (aMajor < bMajor):
    return -1

  elif (aMajor == bMajor):
    if (aMinor < bMinor):
      return -1

    elif (aMinor == bMinor):
      if (aRevision < bRevision):
        return -1

      elif (aRevision == bRevision):
        if (
          ((aQualifier == '') and (bQualifier != ''))
          or (aQualifier < bQualifier)
        ):
          return -1

        elif (aQualifier == bQualifier):
          if (aBuild < bBuild):
            return -1

          elif (aBuild == bBuild):
            return 0

  # if not equal and not lower, then it is bigger :D
  return 1