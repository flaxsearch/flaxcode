=========================
A Guide to the Flax code.
=========================


Introduction
============

This document is a guide to Flax internals. As ever the code is
definitive and the comments in the code can be used to automatically
generate an `api reference`_ (see the comments in the file epydoc.conf
for how to do this). This is more of an overview and will hopefully
help readers to understand how it all fits together.

Some of this document is taken from pages in the wiki. 

.. _`api reference`: file:api/index.html

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

Flax uses the standard `python logging module`_ for logging. A basic
understanding of that module is assumed. 

.. _`python logging module`: http://docs.python.org/lib/module-logging.html

A number of loggers are used in the code (created by calls to
logging.getLogger), and logging calls are made on these. Since Flax is
intended to be a potentially long running process it's convenient to
be able to change the logging output on the fly. To this end each
process that forms part of the system has creates an instance of the
class LogListener_. The main process has an instance of the class
LogConfPub_. This latter has watches the logging configuration file
for changes, and sends an updated version of the file to the
LogListener instances in other processes. These update the logging
configuration accordingly. This mean that changes to the logging
configuration propagate to all parts of the system.

.. _LogListener: file:api/logclient.LogListener-class.html
.. _LogConfPub: file:api/logclient.LogConfPub-class.html
.. _LogConf: file:api/logclient.LogConf-class.html

There is also a mechanism for setting some aspects of the logging
configuration via the web UI (the levels of the top level loggers can
be set). The class LogConf_ supports this by rewriting the logging
configuration file when its .set_levels() method is invoked. Of course
once the file has been written LogConfPub_ will ensure that the changes
propogate to LogListener_ instances as described above.

This combination allows for changes both via the Web UI and via the
logging configuration file in a running system.

A slight wart is that the `python configparser module`_ does not
preserve order or comment on round tripping, we could, in the future,
use the (non-standard) ConfigObj_ module instead to address this.

.. _`python configparser module`: http://docs.python.org/lib/module-ConfigParser.html
.. _ConfigObj: http://www.voidspace.org.uk/python/configobj.html


Cherrypy Logging
~~~~~~~~~~~~~~~~

Cherrypy also uses the logging module but, by default, hardcodes some
apsects of the logging configuration thereby limiting the scope for
using the full flexibility of the logging module's configuration. We
have therefore replaced the default cherrypy logging manager with a
custom one that integrates better with our scheme. This arranges for
cherrypy logging calls to be logged to loggers "webserver.access" and
"webserver.errors".


Indexing
========

In order to build Xapian databases from the files specified by a
document collection Flax has a process that runs separately from the
main web server. This has some advantages:

  * Badly behaved document filters invoked by the indexing process
    need not adversely affect the running of the main web server.

  * The indexer could run on a separate machine from the web server if
    desired to improve performance (this is not possible at the
    moment, but could be acheived with small code changed).

  * On mutlicore processors the indexing process can run on a
    different core from the web service process.

This is no long term state held in the indexer, so that at worst the
current indexing process can be forcably terminated and
restarted. Also the controlling logic for determining when and what to
index depends on the state of document collections and we want to
avoid cross process synchronization issues when such data changes.

The remote indexing process is controlled by an instance of the class
IndexServer_. This creates an instance of the class
IndexProcess_.

.. _IndexServer: file:api/indexserver.indexer.IndexServer-class.html
.. _IndexProcess: file:api/indexserver.indexer.IndexServer-class.html
