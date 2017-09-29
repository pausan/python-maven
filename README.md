= python-maven

This project was initially built to deal with maven repositories and dependencies
for (pyke built tool)[http://pykebuildtool.com]. 

This project is not intended to replace or complement maven in any way,
it is just a library to deal with maven repository and be able to identify 
and download the right artifacts for a java project.

It has been built in a way that it does not depend on pyke to work, but it does
need some external dependencies like (requests)[http://docs.python-requests.org/en/master/] and (xmltodict)[https://github.com/martinblech/xmltodict].

It has only been tested on linux, but I see no reasons why it should not work
on different platforms as well (although I have not tested it yet).

== Examples

At this moment I would advise you to take a look at the tests folders, there
are plenty of unit tests that cover most functionality.

To run the tests
  
  $ cd test
  $ python all.py

== Copyright

Copyright 2017 Pau Sanchez

This software is distributed under MIT license, read LICENSE file for details.