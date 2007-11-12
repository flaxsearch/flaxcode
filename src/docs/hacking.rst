=========================
A Guide to the Flax code.
=========================


Introduction
============

This document is a guide to Flax internals. As ever the code is
definitive and the comments in the code can be used to automatically
generate an `api reference`_ (see the comments in the file epydoc.conf
for how to do this). This is more of an overview and will hopefully
help readers to understand how it all fits together. This document
tries to avoid things that are (or should be) in the end user
documentation, so we assume that readers already know the basics of
how the software works from the user's point of view.

Some of this document is taken from pages in the wiki.

.. _`api reference`: file:api/index.html

Overview
========

The main process runs the webserver which provides a UI for modifying,
creating and deleting document collections, as well as some other
administritave details, and the search forms. It decides when
collections should be indexed and passes requests for indexing off to
a separate indexing process. The indexing process calls filters on
each file of the collection to extract text, which then gets passed to
xapian.

On windows we use the windows indexing service infrastructure to do
the filtering, but we run the IFilters in yet another process, to
guard against badly behaved IFilters bringing the whole system down.


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

The class LogClientProcess_ does most of this for you, although
subclasses must ensure that ``initialise_logging`` is called in their
run methods.

.. _LogClientProcess: file:api/logclient.LogClientProcess-class.html

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


Persistence
===========

The main process save some of its state to a file on exiting, and
every so often (to protect against abnormal termination). This is done
simple by using the standard shelve module to pickle to a file. There
is a separate thread for the periodic saving which 


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

The fields that Flax will attempt to use at some point are as follows:

title The document title. 

    Ideally there should be exactly one block for this field. This is
    rendered in search results so that users have an idea what the
    document might be. If the filter does not yield a block for title
    then some other information relating to the file (e.g. the
    filename, but this might change) will be used for this purpose.

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
   files).

filetype
    The file type of the file. Used when limiting searches to a
    particular type of file. This will probably become obsolete when
    we make use of mimetypes.

mimetype
    The mime type of the data. (Not currently used, but reserved for
    future use.)

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

Separating internal and external fields
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

At the moment there is not check to see if filters are emitting data
for the internal fields. 

For tidiness, and to avoid a potential cause of confusing error
messages, it would be nice to separate out internal fieldnames from
external fieldnames.  This would mean that, even if a filter emitted
an "mtime" field, the value would be indexed differently from the
internal "mtime" field.  This could be achieved by e.g. indexing the
internal fields with a special prefix to distinguish them.


Efficiency
~~~~~~~~~~

Implementing filters as iterators allows for reasonable memory use for
large files - there is no need for filter implementations to hold all
of a file in memory, and there is no need for Flax to hold more than a
block at a time in memory.  However, note that Xapian needs to build
up a complete representation of a document in memory before it can be
indexed, so very large documents are always going to require a
reasonably large amount of memory.

Multiple documents per file
~~~~~~~~~~~~~~~~~~~~~~~~~~~

in the future it may be desirable to change the one-to-one mapping
from files to Xapian documents that we currently have. For example, if
a file is actually an archive of some sort we might want it to yield
document data for each contained file (possibly recursively since an
archive might contain other archives).  This could also be the
situation if we support email mailboxes, in which each email message
should be a separate document (possibly with attachments also as
separate documents).

The current design could be adapted to this kind of situation by
specifying that a filter yields `(docname, docdata-iterator)` were
each `docdata-generator` yields blocks as per the current
specification.  This could be implemented in a backwards compatible
manner in various ways, so doesn't need further investigation at
present.

Custom field types
~~~~~~~~~~~~~~~~~~

In the future a mechanism for defining the treatment of blocks for
other fields may be provided. The issue is essentially one of
determining what the appropriate Xapian field actions for each field,
and providing user interface components to interact with fields that
are not known in advance.

Filter Implementations
======================

This section discusses the filters that have been implemented so
far. Note that currently the file type to filtering mapping is
hardcoded, so the only way to change the actual filter that gets used
for a particular file is to change the code. In future we plan to
include a configuration mechanism for the file type (more generally the
mime type of the data) to filter mapping.


For version 1.0 we intend to support at least the following document
formats on windows:


  * Plain text.
  * HTML.
  * MS Word.
  * MS Excel.
  * MS Power Point.
  * PDF.


It is possible to do this on Windows with a single filter that hooks
into the Windows Indexing Service infrastuture.


IFilter Background
~~~~~~~~~~~~~~~~~~


The IFilter_ interface is designed for this kind of application. There
are some filters implementing this interface for a number of common
document types. IFilters are part of the `Windows Indexing Service`_.

.. _IFilter: http://msdn2.microsoft.com/en-us/library/ms691105.aspx
.. _`Windows Indexing Service`: http://msdn2.microsoft.com/en-us/library/aa163263.aspx


There is a mechanism for determining which filter to use on a given
file. The SDK functions LoadIFilter_, BindIFilterFromStorage_ and
BindIFilterFromStream_ all use information in the registry to
determine which registered filter to use with a particular file. (It
is possible to directly load the dlls, but we do not need to do so now
so this is not discussed further.)

.. _LoadIFilter: http://msdn2.microsoft.com/en-us/library/ms691002.aspx
.. _BindIFilterFromStorage: http://msdn2.microsoft.com/en-us/library/ms690929.aspx
.. _BindIFilterFromStream: http://msdn2.microsoft.com/en-us/library/ms690827.aspx

The filter interface is flexible and appears to work roughly as
follows. Repeated calls to GetChunk_ return STAT_CHUNK_ data. This
provides some information about the current chunk, in particular the
`flags` property, of type CHUNKSTATE_ tells you whether the chunk is
text or some other kind of data. If it is text (`CHUNK_TEXT` is set)
then you can call `GetText_ to get the text from the current
chunk. (Note that each chunk of text can have a different locale , so
from this perspective language is not per-document, but per-chunk.)
STAT_CHUNK_ also has a property `attribute` which gives more
information about the chunk, which provides for mapping chunk contents
to particular xapian fields.

.. _STAT_CHUNK: http://msdn2.microsoft.com/en-us/library/ms691016.aspx
.. _CHUNKSTATE: http://msdn2.microsoft.com/en-us/library/ms691020.aspx
.. _GetChunk: http://msdn2.microsoft.com/en-us/library/ms691080.aspx
.. _GetText: http://msdn2.microsoft.com/en-us/library/ms690992.aspx

The chunk may additionally, or alternatively have `CHUNK_VALUE`
set. In this case calling GetValue_ gets the value. This can yield any
kind of data.  It could be that there is useful text embedded with
these chunks, but the practicability of extracting the text depends on
determining the format of the data and having a filter for such
data. In the first instance it might be wise to ignore value chunks
and see what kind of results we get by just looking at text chunks.

.. _GetValue: http://msdn2.microsoft.com/en-us/library/ms690927.aspx

There are some code generic code samples_ that demonstrating using
this api some of this infrastucture

.. _samples: http://msdn2.microsoft.com/en-us/library/ms689723.aspx

IFilter filter
~~~~~~~~~~~~~~


The current `ifilter filter`_ started out as a modified verion of the
an example_ of using IFilters via COM in the `python windows
extensions`_.

.. _example: http://pywin32.cvs.sourceforge.net/pywin32/pywin32/com/win32comext/ifilter/demo/filterDemo.py?view=markup
.. _`python windows extensions`: http://sourceforge.net/projects/pywin32/
.. _`ifilter filter`: file:api/indexserver.w32com_ifilter-module.html#ifilter_filter

This works reasonably well, although we seem to get quite a few
exceptions with pdf files for reasons that are not entirely clear.


Simple Text Filter
~~~~~~~~~~~~~~~~~~

For text documents, for testing, and for non-windows platforms it is
convenient to have a simple filter for text files. This has been
implemented_.

.. _implemented: file:api/indexserver.simple_text_filter-module.html#simple_text_filter


HtmltoText Filter
~~~~~~~~~~~~~~~~~


The Xapian html has been split off and packaged separately as the
htmltotext_ package. This is used by the html_filter_.

.. _htmltotext: http://pypi.python.org/pypi/htmltotext/0.6
.. _html_filter: file:api/indexserver.htmltotext_filter-module.html#html_filter


PyPdf Filter
~~~~~~~~~~~~

Here_ is a simple filter using PyPdf_, but in practice the current
version throws rather too many exceptions to be generally useful.

.. _Here: file:api/indexserver.pypdf_filter-module.html#pdf_filter
.. _PyPdf: http://pybrary.net/pyPdf/

Other document filters
~~~~~~~~~~~~~~~~~~~~~~


Eventually we will need non-IFilter mechanisms for parsing documents
on non-Windows platforms. The formats that are likely to give the most
trouble are MS Office.  Antiword_ is one way of extracting text from
word documents. Also OpenOffice_ can parse MS Office documents and
also has python bindings, which can be used to extract text - see
this_ example.

.. _Antiword: http://www.winfield.demon.nl/
.. _OpenOffice: http://www.openoffice.org/
.. _this: http://udk.openoffice.org/python/samples/ooextract.py 


Xapian's "omindex" tool has support for indexing from lots of document
formats using unix tools - we should copy at least some of the filter
invocations it uses rather than figuring them out from scratch.  Mostly,
these involve invoking a sub-process to perform the filtering.

