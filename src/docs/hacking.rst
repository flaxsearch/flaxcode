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
IndexServer_. This creates an instance of the class IndexProcess_, and
determines when document collections get indexed. This is determined
as follows. Each document collection has properties ``indexing_due``
and ``indexing_held``. If a the former is true, and the latter false
then the collection is eligible for indexing. The code searches for
eligible collections and starts indexing on the first it finds. This
search happens whenever an indexing of a collection terminates, or
when the ``indexing_due`` or ``indexing_held`` state of a collection
is modified using one of the methods intended for this purpose:
``hold_indexing``, ``unhold_indexing``, ``set_due``, ``unset_due``, or
the convenience method ``toggle_due_or_held``.

If there is a collection eligible then one should be in the process of
being indexed. Currently no more than one collection can be indexed at
any one time. It would be relatively simple to adapt the code to
control a pool of indexing processes and allow for multiple
simulatanous indexings, which might improve performance, especially on
multicore processors, or if we allowed for indexing processes to run
on separate machines.

.. _IndexServer: file:api/indexserver.indexer.IndexServer-class.html
.. _IndexProcess: file:api/indexserver.indexer.IndexServer-class.html


The actual indexing involves making calls on Xapian_ (via Xappy_) to
make (or update) a database for the collection. The document
collection itself determines which files should be considered for
indexing, and for each file type there is a filter__ that extracts the
text content of the file. In the current implementation the file type
to filter mapping is fixed (for each operating system) but in the
future we plan to allow this mapping to be configured.

.. __: Filters_

Filters
~~~~~~~

A filter is a python callable (a function or an object that implements
``__call__``) that takes a filename and returns an iterator that
yields ``(fieldname, value)`` pairs, where ``fieldname`` names the
field to which the ``value`` is to be added. Each such pair may be
referred to as a "block" for ``fieldname``.

Flax only takes note of a certain predefined fields, as mentioned
below. Filters should avoid emitting blocks for other fields: if a
non-predefined field is emitted, a warning message will be placed in
the indexing log, and the field text will be ignored.  An error will
not be raised, so that indexing of the document can complete.

This allows a filter designed for a different versions of Flax to be
used with a version of Flax which doesn't define a particular field,
but avoids silently ignoring input data.

Flax does minimal checking of the blocks returned by filters, and will
tolerate significant deviation from the guidelines below (checking
would slow down the indexing process, and make compatibility between
versions of Flax harder), but if filters do not follow these
guidelines then the quality of search results might be lessened. The
filters that are distributed as part of Flax all comply with these
guidelines.

The fields that Flax notices are as follows:

title
    The document title. Ideally there should be exactly one block for
    this field. If there is no block for this then Flax will provide a
    default block based on something like the filename, URI or first
    content block emitted by the filter (but filter writers shouldn't
    rely on any particular behaviour here).

content
    Text for the main contents of the document. ``content`` blocks
    should be emitted in paragraphs. Phrase and adjacency searches
    take note of paragraphs. For example, if a filter emits blocks:
    ``('content', 'Aardvark ')`` followed by ``('content', 'soup')``,
    then a search for the phrase ``"Aardvark soup"`` will
    fail. However if a filter emits ``('content', 'Aardvark soup')``
    then the same search will succeed. (This is not necessarily an
    argument for aggregating blocks together.)

description
    General descriptive text about the document. Filters may emit
    several blocks for this field. Text should be emitted in
    paragraphs.

keyword
    A keyword for the document. The content for each block should be a
    single word describing the document.  Many document formats have a
    way to store keywords for a particular document, which users may
    use in various different ways - this field allows users to search
    based on them.

Note that the Flax infrastructure uses the following fields. Filters
should not emit blocks for these:

filename
   The operating system filename for the file (only used for local
   files)

filetype
    The file type of the file. Used when limiting searches to a
    particular type of file. This will probably become obsolete when
    we make use of mimetypes.

mimetype
    Not currently used, but reserved for future use.

uri
   URI for the file (not currently used, but reserved for future use).

nametext
   Text extracted from the filename.  Currently, this is just the
   basename of the file, but later we may want to perform various word
   splitting algorithms, and use other parts of the path.

mtime
   The time at which the file was last modified (note: this is not the
   time when it was last indexed), as returned by the standard python
   funtion ``os.path.getmtime``.

size
   The size of the file (in bytes).

collection
   The document collection that the document belongs too. (Note that
   the same source file might form part of different document
   settings, but this will give rise to different (Xapian) documents
   within the document collection databases.)

