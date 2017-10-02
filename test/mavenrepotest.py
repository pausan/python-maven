#!/usr/bin/env python
# -*- coding: utf-8 -*- 
import os,sys
import unittest

sys.path.append (os.path.join (os.path.dirname (__file__), '..'))

from mavencoord import MavenCoord
from mavenrepo import MavenRepo

class MavenRepoTest (unittest.TestCase):
  """ Test fetching dependencies on any maven repository

  If you want to add more tests feel free to prepare a pom.xml with
  ceritain dependencies and resolve them with any of these commands:

    $ mvn dependency:tree -DoutputType=text 
    $ mvn dependency:tree -DoutputType=text -Doutput=deps.txt

  """
  def testFetchNonExisting (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    maven = repo.fetchOne ('commons-io:commons-io:1.4.4.2')
    self.assertEquals (maven, None)
    return 

  def testFetchOneWithVersion (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    maven = repo.fetchOne ('commons-io:commons-io:2.4')
    self.assertEquals (maven.coord.id, 'commons-io:commons-io:2.4')
    self.assertEquals (maven.deps.getFlattenCoordIds(), ['junit:junit:4.10'])
    return 

  def testFetchWithLatestVersion (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    maven = repo.fetchOne ('commons-io:commons-io')
    self.assertEquals (maven.coord.id, 'commons-io:commons-io:2.5')
    self.assertEquals (maven.deps.getFlattenCoordIds(), ['junit:junit:4.12'])
    return

  def testFetchSimpleWithAncestors (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    maven = repo.fetchWithAncestors ('commons-io:commons-io')
    self.assertEquals (maven.coord.id, 'commons-io:commons-io:2.5')
    self.assertEquals (maven.deps.getFlattenCoordIds(), ['junit:junit:4.12'])
    return

  def testFetchWithAncestors (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    maven = repo.fetchWithAncestors ('org.apache.cxf:cxf-rt-frontend-jaxws:3.0.2')
    self.assertEquals (maven.coord.id, 'org.apache.cxf:cxf-rt-frontend-jaxws:3.0.2')

    maven.resolve()

    self.assertEquals (
      [x.id for x in maven.deps.getFlattenCoords () if x.scope == 'provided'],
      [
        u'org.osgi:org.osgi.core:4.2.0'
      ]
    )

    self.assertEquals (
      [x.id for x in maven.deps.getFlattenCoords () if x.scope == 'compile'],
      [
        u'xml-resolver:xml-resolver:1.2',
        u'asm:asm:3.3.1',
        u'org.apache.cxf:cxf-core:3.0.2',
        u'org.apache.cxf:cxf-rt-bindings-soap:3.0.2',
        u'org.apache.cxf:cxf-rt-bindings-xml:3.0.2',
        u'org.apache.cxf:cxf-rt-frontend-simple:3.0.2',
        u'org.apache.cxf:cxf-rt-ws-addr:3.0.2'
      ]
    )

    self.assertEquals (
      [x.id for x in maven.deps.getFlattenCoords () if x.scope == 'test'],
      [
        u'junit:junit:4.11',
        u'org.easymock:easymock:3.1',
        u'org.apache.cxf:cxf-testutils:3.0.2',
        u'org.apache.cxf:cxf-rt-transports-http:3.0.2',
        u'org.apache.cxf:cxf-rt-ws-policy:3.0.2',
        u'org.apache.geronimo.specs:geronimo-javamail_1.4_spec:1.7.1',
        u'org.slf4j:jcl-over-slf4j:1.7.7',
        u'org.slf4j:slf4j-jdk14:1.7.7',
      ]
    )
    return

  def testFetchTreeForJUnit (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    maven = repo.fetchResolvedTree ('junit:junit:4.11', 'compile')
    maven.resolve(scope = 'compile')
    self.assertEquals (
      maven.deps.getFlattenCoordFullIds (),
      [
        u'org.hamcrest:hamcrest-core:jar:1.3:compile'
      ]
    )
    return

  def testFetchTreeForCxfCore (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    maven = repo.fetchResolvedTree ('org.apache.cxf:cxf-core:3.0.2', 'compile')
    maven.resolve(scope = 'compile')
    self.assertEquals (
      maven.deps.getFlattenCoordFullIds (),
      [
        'org.codehaus.woodstox:woodstox-core-asl:jar:4.4.1:compile',
        'org.codehaus.woodstox:stax2-api:jar:3.1.4:compile',
        'org.apache.ws.xmlschema:xmlschema-core:jar:2.1.0:compile',
      ]
    )
    return

  def testFetchTreeForCxfDatabinding (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    repo.setJdkVersion ('1.8') # different versions will change the result

    maven = repo.fetchResolvedTree ('org.apache.cxf:cxf-rt-databinding-jaxb:3.0.2', 'compile')
    maven.resolve(scope = 'compile')
    self.assertEquals (
      maven.deps.getFlattenCoordFullIds (),
      [
        'org.apache.cxf:cxf-core:jar:3.0.2:compile',
        'org.codehaus.woodstox:woodstox-core-asl:jar:4.4.1:compile',
        'org.codehaus.woodstox:stax2-api:jar:3.1.4:compile',
        'org.apache.ws.xmlschema:xmlschema-core:jar:2.1.0:compile',
        'org.apache.cxf:cxf-rt-wsdl:jar:3.0.2:compile',
        'wsdl4j:wsdl4j:jar:1.6.3:compile',
        'asm:asm:jar:3.3.1:compile',
        'com.sun.xml.bind:jaxb-impl:jar:2.2.10-b140310.1920:compile',
        'com.sun.xml.bind:jaxb-core:jar:2.2.10-b140310.1920:compile',
      ]
    )
    return

  def testFetchTreeForCxfRtWsPolicy (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    repo.setJdkVersion ('1.8') # different versions will change the result

    maven = repo.fetchResolvedTree ('org.apache.cxf:cxf-rt-ws-policy:3.0.2', 'compile')
    maven.resolve(scope = 'compile')

    self.assertEquals (
      maven.deps.getFlattenCoordFullIds (),
      [x.strip() for x in [
        'wsdl4j:wsdl4j:jar:1.6.3:compile',
        'org.apache.cxf:cxf-core:jar:3.0.2:compile',
        '  org.codehaus.woodstox:woodstox-core-asl:jar:4.4.1:compile',
        '    org.codehaus.woodstox:stax2-api:jar:3.1.4:compile',
        '  org.apache.ws.xmlschema:xmlschema-core:jar:2.1.0:compile',
        'org.apache.neethi:neethi:jar:3.0.3:compile',
      ]]
    )
    return

  def testFetchTreeForCxfRtFrontendJaxws (self):
    repo = MavenRepo (MavenRepo.OFFICIAL_REPO_URL)
    repo.setJdkVersion ('1.8') # different versions will change the result

    maven = repo.fetchResolvedTree ('org.apache.cxf:cxf-rt-frontend-jaxws:3.0.2', 'compile')
    maven.resolve(scope = 'compile')

    self.assertEquals (
      maven.deps.getFlattenCoordFullIds (),
      [x.strip() for x in [
        'xml-resolver:xml-resolver:jar:1.2:compile',
        'asm:asm:jar:3.3.1:compile',
        'org.apache.cxf:cxf-core:jar:3.0.2:compile',
        '  org.codehaus.woodstox:woodstox-core-asl:jar:4.4.1:compile',
        '    org.codehaus.woodstox:stax2-api:jar:3.1.4:compile',
        '  org.apache.ws.xmlschema:xmlschema-core:jar:2.1.0:compile',
        'org.apache.cxf:cxf-rt-bindings-soap:jar:3.0.2:compile',
        '  org.apache.cxf:cxf-rt-wsdl:jar:3.0.2:compile',
        '    wsdl4j:wsdl4j:jar:1.6.3:compile',
        '  org.apache.cxf:cxf-rt-databinding-jaxb:jar:3.0.2:compile',
        '    com.sun.xml.bind:jaxb-impl:jar:2.2.10-b140310.1920:compile',
        '    com.sun.xml.bind:jaxb-core:jar:2.2.10-b140310.1920:compile',
        'org.apache.cxf:cxf-rt-bindings-xml:jar:3.0.2:compile',
        'org.apache.cxf:cxf-rt-frontend-simple:jar:3.0.2:compile',
        'org.apache.cxf:cxf-rt-transports-http:jar:3.0.2:compile',
        'org.apache.cxf:cxf-rt-ws-addr:jar:3.0.2:compile',
        'org.apache.cxf:cxf-rt-ws-policy:jar:3.0.2:compile',
        '  org.apache.neethi:neethi:jar:3.0.3:compile',
      ]]
    )
    
if __name__ == '__main__':
  unittest.main() 

