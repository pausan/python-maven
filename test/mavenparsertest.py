#/usr/bin/env python
# -*- coding: utf-8 -*- 
import os,sys
import unittest

sys.path.append (os.path.join (os.path.dirname (__file__), '..'))

from mavencoord import MavenCoord
from mavendeps import MavenDep, MavenDeps
import mavenparser 

class MavenParserTest (unittest.TestCase):

  def _checkSimpleMaven(self, simple):
    self.assertTrue (simple.parent.empty())
    self.assertEquals (simple.coord.id, 'org.codehaus.mojo:my-project:1.0')
    self.assertEquals (simple.deps.count(), 1)
    self.assertEquals (simple.deps.getFlattenCoordIds(), ['junit:junit:4.0-RELEASE'] )
    return

  def testSimpleString (self):
    with open ('data/simple.xml', 'rb') as f:
      mvn = mavenparser.parseString (f.read ())
      self._checkSimpleMaven (mvn)
    return

  def testSimpleFile (self):
    mvn = mavenparser.parseFile ('data/simple.xml')
    self._checkSimpleMaven (mvn)
    return

  def testParentTagInheritance (self):
    """ test that inherits some attributes from parent tag (like group and version)
    """
    mvn = mavenparser.parseFile ('data/parent-tag-inheritance.xml')
    self.assertEquals (mvn.parent.id, 'org.mygroup.something:my-parent:v1.2')
    self.assertEquals (mvn.coord.id,  'org.mygroup.something:my-project:v1.2')
    self.assertEquals (mvn.deps.count(), 2)

    self.assertEquals (mvn.deps.getFlattenCoordIds(skipOptional = True), [
      'junit:junit:4.0-RELEASE'
    ])

    self.assertEquals (mvn.deps.getFlattenCoordIds(skipOptional = False), [
      'junit:junit:4.0-RELEASE',
      'org.mockito:mockito-all:1.9.5'
    ])
    return

  def testParseExclusionsAndClone (self):
    mvn = mavenparser.parseFile ('data/logging-exclusion.xml')

    for mvnObj in [mvn, mvn.clone()]:
      self.assertEquals (mvnObj.parent.id, 'com.gamehouse.metapackages:parent:20150115.103.1')
      self.assertEquals (mvnObj.coord.id,  'com.gamehouse.metapackages:logging:20150115.103.1')
      self.assertEquals (mvnObj.deps.count(), 7)

      self.assertEquals (mvnObj.deps.getFlattenCoordIds (skipOptional = True), [
        'com.splunk:logging:1.0',
        'commons-logging:commons-logging:99.0-does-not-exist',
        'log4j:log4j:1.2.17',
        'name.caiiiycuk.scribe:scribe-log4j:1.0',
        'org.slf4j:jcl-over-slf4j:1.7.10',
        'org.slf4j:slf4j-api:1.7.10',
        'org.slf4j:slf4j-log4j12:1.7.10'      
      ])

      # check exclusions
      self.assertEquals (
        [x.id for x in mvnObj.deps.find ('com.splunk:logging:1.0').exclusions], [
        'org.slf4j:slf4j-jdk14:',
        'ch.qos.logback:logback-core:',
        'ch.qos.logback:logback-classic:'
      ])
      
      self.assertEquals (
        [x.id for x in mvnObj.deps.find ('name.caiiiycuk.scribe:scribe-log4j:1.0').exclusions], 
        ['javax.servlet:servlet-api:']
      )

      self.assertEquals (
        mvnObj.deps.find ('commons-logging:commons-logging:99.0-does-not-exist').exclusions,
        []
      )
    return

  def testProfilesAllDisabled (self):
    mvn = mavenparser.parseFile ('data/profiles/disabled-by-default.xml')

    self.assertTrue (mvn.parent.empty())
    self.assertEquals (mvn.coord.id,  'com.mycompany.app:my-app:1.0-SNAPSHOT')
    self.assertEquals (mvn.deps.count(), 2)
    
    mvn.resolve()

    self.assertEquals (mvn.deps.getFlattenCoordIds (), [
      'org.apache.cxf:cxf-core:1.0.0',
      'junit:junit:4.10',
    ])    
    return

  def testProfilesEnabledByDefault (self):
    mvn = mavenparser.parseFile ('data/profiles/enabled-by-default.xml')

    self.assertTrue (mvn.parent.empty())
    self.assertEquals (mvn.coord.id,  'com.mycompany.app:my-app:1.0-SNAPSHOT')
    self.assertEquals (mvn.deps.count(), 2)
    
    mvn.resolve()

    self.assertEquals (mvn.deps.getFlattenCoordIds (), [
      'org.apache.cxf:cxf-core:3.0.2',
      'junit:junit:4.11',
    ])    
    return 

  def testProfilesEnabledByJdk (self):
    mvn = mavenparser.parseFile ('data/profiles/enabled-by-jdk.xml')

    self.assertTrue (mvn.parent.empty())
    self.assertEquals (mvn.coord.id,  'com.mycompany.app:my-app:1.0-SNAPSHOT')
    self.assertEquals (mvn.deps.count(), 2)
    
    mvn1 = mvn.clone()
    mvn2 = mvn.clone()

    # resolve using a JDK version that does not enable the profile
    mvn1.resolve (jdkVersion = '1.6')

    self.assertEquals (mvn1.deps.getFlattenCoordIds (), [
      'org.apache.cxf:cxf-core:1.0.0',
      'junit:junit:4.10'
    ])   

    # resolve using a JDK version that enables the profile
    mvn2.resolve (jdkVersion = '1.9')

    self.assertEquals (mvn2.deps.getFlattenCoordIds (), [
      'org.apache.cxf:cxf-core:3.0.2',
      'junit:junit:4.11',
    ])

    return

  def testProfilesEnabledByProperty(self):
    mvn = mavenparser.parseFile ('data/profiles/enabled-by-property.xml')

    self.assertTrue (mvn.parent.empty())
    self.assertEquals (mvn.coord.id,  'com.mycompany.app:my-app:1.0-SNAPSHOT')
    self.assertEquals (mvn.deps.count(), 2)
    
    mvn1 = mvn.clone()
    mvn2 = mvn.clone()
    mvn3 = mvn.clone()

    # resolve with no property set
    mvn1.resolve ()

    self.assertEquals (mvn1.deps.getFlattenCoordIds (), [
      'org.apache.cxf:cxf-core:1.0.0',
      'junit:junit:4.10'
    ])   
    
    # resolve with a property with the wrong value
    mvn2.setProperty ('my.property', 'wrong-value')
    mvn2.resolve ()

    self.assertEquals (mvn2.deps.getFlattenCoordIds (), [
      'org.apache.cxf:cxf-core:1.0.0',
      'junit:junit:4.10'
    ])   

    # resolve using a JDK version that enables the profile
    mvn3.setProperty ('my.property', 'right-value')
    mvn3.resolve (jdkVersion = '1.9')

    self.assertEquals (mvn3.deps.getFlattenCoordIds (), [
      'org.apache.cxf:cxf-core:3.0.2',
      'junit:junit:4.11',
    ])

    return

  def testDependencyManagement (self):
    """ Test complex apache CXF module previously downloaded
    """ 
    mvn1 = mavenparser.parseFile ('data/org.apache.cxf/cxf-rt-frontend-jaxws-3.0.2.pom')
    mvn2 = mavenparser.parseFile ('data/org.apache.cxf/cxf-parent-3.0.2.pom')
    
    mvn1.merge (mvn2)

    mvn1.resolve ()

    self.assertEquals (
      [x.id for x in mvn1.deps.getFlattenCoords () if x.scope == 'provided'],
      [
        u'org.osgi:org.osgi.core:4.2.0'
      ]
    )

    self.assertEquals (
      [x.id for x in mvn1.deps.getFlattenCoords () if x.scope == 'compile'],
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
      [x.id for x in mvn1.deps.getFlattenCoords () if x.scope == 'test'],
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


  def testComplexApacheCxf (self):
    """ Test complex apache CXF module previously downloaded
    """ 
    mvn1 = mavenparser.parseFile ('data/org.apache.cxf/cxf-rt-frontend-jaxws-3.0.2.pom')
    mvn2 = mavenparser.parseFile ('data/org.apache.cxf/cxf-parent-3.0.2.pom')
    mvn3 = mavenparser.parseFile ('data/org.apache.cxf/cxf-3.0.2.pom')

    mvn1.merge (mvn2)
    mvn1.merge (mvn3)

    # after the merge, without property expansion
    self.assertEquals (
      mvn1.deps.getFlattenCoordIds (),
      [
        u'org.osgi:org.osgi.core:',
        u'junit:junit:',
        u'org.easymock:easymock:',
        u'org.apache.cxf:cxf-testutils:${project.version}',
        u'xml-resolver:xml-resolver:',
        u'${cxf.asm.groupId}:${cxf.asm.artifactId}:',
        u'org.apache.cxf:cxf-core:${project.version}',
        u'org.apache.cxf:cxf-rt-bindings-soap:${project.version}',
        u'org.apache.cxf:cxf-rt-bindings-xml:${project.version}',
        u'org.apache.cxf:cxf-rt-frontend-simple:${project.version}',
        u'org.apache.cxf:cxf-rt-transports-http:${project.version}',
        u'org.apache.cxf:cxf-rt-ws-addr:${project.version}',
        u'org.apache.cxf:cxf-rt-ws-policy:${project.version}',
        u'org.apache.geronimo.specs:geronimo-javamail_1.4_spec:',
        u'org.slf4j:jcl-over-slf4j:',
        u'org.slf4j:slf4j-jdk14:'
      ]
    )    

    mvn1.expand()
    
    self.assertEquals (
      mvn1.deps.getFlattenCoordIds (),
      [
        u'org.osgi:org.osgi.core:',
        u'junit:junit:',
        u'org.easymock:easymock:',
        u'org.apache.cxf:cxf-testutils:3.0.2',
        u'xml-resolver:xml-resolver:',
        u'asm:asm:',
        u'org.apache.cxf:cxf-core:3.0.2',
        u'org.apache.cxf:cxf-rt-bindings-soap:3.0.2',
        u'org.apache.cxf:cxf-rt-bindings-xml:3.0.2',
        u'org.apache.cxf:cxf-rt-frontend-simple:3.0.2',
        u'org.apache.cxf:cxf-rt-transports-http:3.0.2',
        u'org.apache.cxf:cxf-rt-ws-addr:3.0.2',
        u'org.apache.cxf:cxf-rt-ws-policy:3.0.2',
        u'org.apache.geronimo.specs:geronimo-javamail_1.4_spec:',
        u'org.slf4j:jcl-over-slf4j:',
        u'org.slf4j:slf4j-jdk14:'
      ]
    )

  
if __name__ == '__main__':
  unittest.main()
