=========================
A Guide to the Flax code.
=========================


Introduction
============

This document is a guide to Flax internals. As ever the code is
definitive and the comments in the code can be used to automatically
generate an api reference. This is more of an overview and will
hopefully help understand how it all fits together.

Components
==========

Flax is implemented in python_ and uses a number of third party
libraries, and some understanding of the way they work will aid
understanding of Flax. These are detailed below.

.. _python: http://www.python.org

Cherrypy
~~~~~~~~

Cherrypy is a web server framework. We use it for all the HTTP
interaction with web browsers. The code in cpserver.py implements the
"applications" (as cherrypy calls them) for this. http://www.cherrypy.org/.

HTMLTemplate
~~~~~~~~~~~~

This is a simple templating engine. The actual templates are the files
with .html extentions in templates/, although they are not actually
well formed html. The code in templates.py loads these templates and
renders them. Calls on these are made from the webserving code in
cpserver.py. http://freespace.virgin.net/hamish.sanderson/htmltemplate.html

Processing
~~~~~~~~~~

The processing module is used for creating processeses and dealing
with interprocess
communication. http://developer.berlios.de/projects/pyprocessing

HTMLToText
~~~~~~~~~~

This is used to extract text from html. http://pypi.python.org/pypi/htmltotext/0.6.

Xappy
~~~~~

Xappy is a high level interface python interface to xapian. http://xappy.org/

Xapian
~~~~~~

Xapian is a search engine library. http://www.xapian.org/

Py2exe.
~~~~~~~

Python Windows extentions. http://sourceforge.net/projects/pywin32/

MochiKit
~~~~~~~~

http://www.mochikit.com/





Document Collections
====================

The central object in Flax is the document collection (see the class
DocCollection) - such has a number of purposes:

 - Specifying the set of documents that make up the document
   collection (see the class FileSpec).

 - Specifying how xapian databases for the collection are configured
   (see the class DBSpec)

 - Specifying when automatic indexing of the collection takes place
   (see the class ScheduleSpec).

 - Defining mapping for files in the collection to urls. (This should
   perhaps be part of FileSpec, but it's not done that way at the
   moment.)

Logging.
========

Flax uses the standard python logging module for logging. A basic
understanding of that module is assumed. See:
http://docs.python.org/lib/module-logging.html.

A number of loggers are used in the code (created by calls to
logging.getLogger), and logging calls are made on these. Since Flax is
intended to be a potentially long running process it's convenient to
be able to change the logging output on the fly. To this end each
process that forms part of the system has creates an instance of the
class logclient.LogListener. The main process has an instance of the
class logclient.LogConfPub. This latter has watches the logging
configuration file for changes, and sends an updated version of the
file to the LogListener instances in other processes. These update the
logging configuration accordingly. This mean that changes to the
logging configuration propagate to all parts of the system.

There is also a mechanism for setting some aspects of the logging
configuration via the web UI (the levels of the top level loggers can
be set). The class logclient.LogConf supports this by rewriting the
logging configuration file when its .set_levels() method is
invoked. Of course once the file has been written LogConfPub will
ensure that the changes propogate to rge LogListener instances as
described above.

This combination allows for changes both via the Web UI and via the
logging configuration file in a running system.

Cherrypy Logging
~~~~~~~~~~~~~~~~

Cherrypy also uses the logging module but, by default, hardcodes some
logging calls thereby limiting the scope for using the full
flexibility of the logging module's configuration. We have therefore
replaces the default cherrypy logging manager with a custom one that
integrates better with our scheme. This arranges for cherrypy logging
calls to be logged to loggers "webserver.access" and
"webserver.errors".



