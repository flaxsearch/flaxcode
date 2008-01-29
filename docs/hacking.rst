=========================
A Guide to the Flax code.
=========================


Introduction
============

This document is a guide to Flax internals. As ever the code is
definitive and the comments in the code can be used to automatically
generate an `API reference`_ (see the comments in the file epydoc.conf
for how to do this). This is more of an overview and will hopefully
help readers to understand how it all fits together. This document
tries to avoid things that are (or should be) in the end user or api
documentation, so we assume that readers already know the basics of
how the software works from the user's point of view.

Some of this document has been taken from pages that lived on the
wiki_, to avoid duplication and inconsistencies those pages have been
removed, but are still accessible via subversion.

.. _`API reference`: ./api/index.html
.. _wiki: http://code.google.com/p/flaxcode/w/list

Overview
========

The main process runs the web server which provides a UI for
modifying, creating and deleting document collections, as well as some
other administrative details, and the search forms. It decides when
collections should be indexed and passes requests for indexing off to
a separate indexing process. The indexing process calls filters on
each file of the collection to extract text, which then gets passed to
Xapian.

On Windows we use the Windows indexing service infrastructure to do
the filtering, but we run the IFilters in yet another process, to
guard against badly behaved IFilters bringing the whole system down.


Components
==========

Flax is implemented in python_ and uses a number of third party
libraries, and some understanding of the way they work will aid
understanding of Flax. These are listed below (in no particular
order).

.. _python: http://www.python.org

  - Cherrypy. Cherrypy_ is a web server framework. We use it for all
    the HTTP interaction with web browsers. The code in cpserver.py
    implements the "applications" (as Cherrypy calls them) for
    this.

  - HTMLTemplate_: This is a simple templating engine. The actual
    templates are the files with .html extensions in templates/,
    although they are not actually well formed HTML. The code in
    templates.py loads these templates and renders them. Calls on
    these are made from the web-serving code in cpserver.py.

  - Processing_. The processing module is used for creating processes
    and dealing with inter-process communication.

  - HTMLToText_. This is used to extract text from HTML.

  - Xappy_. A high level interface python interface to Xapian.

  - Xapian_. A search engine library.

  - Py2exe_. Software to convert python programs to windows
    executables.

  - `Python Windows extensions`_. Python modules to hook into a lot of
    the Windows api, in particular allowing for fairly simple client
    side COM programming in python. Obviously modules from this
    package are only required when running on Windows.

  - MochiKit_. A javascript library

.. _CherryPy: http://www.cherrypy.org/
.. _HTMLTemplate: http://freespace.virgin.net/hamish.sanderson/htmltemplate.html
.. _Processing: http://developer.berlios.de/projects/pyprocessing
.. _HTMLToText: http://pypi.python.org/pypi/htmltotext/0.6
.. _Xappy: http://xappy.org/
.. _`Python Windows extensions`: http://sourceforge.net/projects/pywin32/
.. _Xapian: http://www.xapian.org/
.. _MochiKit: http://www.mochikit.com/
.. _Py2exe: http://www.py2exe.org/

These libraries are either included in the flax subversion repository,
or else can be installed by running the script
``utils\install_dependencies.py``. This will download and each of
these libraries and place them in a location that the Flax code itself
will add to ``sys.path``.  Flax has been developed using the versions
of these libraries that this script installs; using other versions may
lead to problems.


Document Collections
====================

The central object in Flax is the document collection (see the class
DocCollection_) - such has a number of purposes:

 - Specifying the set of documents that make up the document
   collection (see the class FileSpec_). The code is self explanatory
   really; note that the ``.files()`` method of the class returns a
   generator.

 - Specifying how Xapian_ databases for the collection are configured
   (see the class DBSpec_). The configuration possibilities provided
   by the code are not exposed via the web UI in the current version.

 - Specifying when automatic indexing of the collection takes place
   (see the class ScheduleSpec_). The current scheme is a simplified
   cron style system.

 - Defining mapping for files in the collection to URLs. (This should
   perhaps be part of FileSpec_, but it's not done that way at the
   moment.) If there's not web server available to serve the files (or
   it's inconvenient so configure one), then for testing and
   development it's often useful to configure the mapping as a
   "file://" url for the corresponding path.

.. _DocCollection: ./api/doc_collection.DocCollection-class.html
.. _FileSpec: ./api/filespec.FileSpec-class.html
.. _DBSpec: ./api/dbspec.DBSpec-class.html
.. _ScheduleSpec: ./api/schedulespec.ScheduleSpec-class.html

Document collections are created and modified via the web UI. The
scheduling is implemented via a simple loop running in a separate
thread that checks every minute to see which collections are due to be
indexed - see the class ScheduleIndexing_. Obviously we could make
this do this in a more efficient way, but it's probably not
significant unless there are rather more document collections that we
would normally expect.

.. _ScheduleIndexing: ./api/scheduler.ScheduleIndexing-class.html


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
propagate to LogListener_ instances as described above.

If people configure loggers via the configuration file then it is
possible for the UI configuration to be a little misleading, since
only the "first level" loggers (those immediately below the root
logging in the hierarchy) appear in the UI, and the configuration file
could change the setting for loggers below these so that they no
longer follow the settings for the logger above them.  However, since
the same people should be responsible for both, the current
arrangement is a reasonable compromise given the desires to provide
the full configuration possibilities and also to have a relatively
simple, yet useful, option available in the UI.

At the time of writing the following loggers are used by the code,
there is no point in configuring other loggers unless you add code
that uses them:

  - webserver
  - webserver.errors
  - webserver.access
  - scheduling
  - collections
  - indexing
  - filtering.ifilter
  - indexing
  - indexing
  - searching



The class LogClientProcess_ ensure that subclass processes receive
updates to the global logging configuration, although subclasses must
ensure that ``initialise_logging`` is called in their run methods.

.. _LogClientProcess: file:api/logclient.LogClientProcess-class.html

This combination allows for changes both via the Web UI and via the
logging configuration file in a running system.

A slight wart is that the `python configparser module`_ does not
preserve order or comment on round tripping, we could, in the future,
use the (non-standard) ConfigObj_ module instead to address this.

.. _`python configparser module`: http://docs.python.org/lib/module-ConfigParser.html
.. _ConfigObj: http://www.voidspace.org.uk/python/configobj.html

Note that the same configuration file is used to configure loggers in
different processes, and there is no mechanism for synchronizing
access to underlying IO across processes. The is typically not a
problem except in the case of RotatingFileHandler_ or
TimedRotatingFileHandler_, since (on windows at least) attempting to
perform the rotation when other process have open file handles on the
files will cause an exception. To deal with this we have implemented a
subclass of RotatingFileHandler_ that does not actually open files
until it has events to log. Provided the configuration is such that
the same logger (i.e. loggers with a particular name) are not used
from more than one process everything is OK.

.. _RotatingFileHandler: http://docs.python.org/lib/node413.html
.. _TimedRotatingFileHandler: http://docs.python.org/lib/node414.html

(The logging configuration is fairly self contained and could probably
be split out into a separate python package to be used in other
multi-process applications.)

Cherrypy Logging
~~~~~~~~~~~~~~~~

Cherrypy also uses the logging module but, by default, hard codes some
aspects of the logging configuration thereby limiting the scope for
using the full flexibility of the logging module's configuration. We
have therefore replaced the default Cherrypy logging manager with a
custom one that integrates better with our scheme. This arranges for
Cherrypy logging calls to be logged to loggers "webserver.access" and
"webserver.errors". (Note that this requires a small amount of
duplication of some Cherrypy internals in our code, and if the way
Cherrypy does its logging changes in future versions we might need
change the implementation of the class cpLogger_.)

.. _cpLogger: ./api/cplogger.cpLogger-class.html


Persistence
===========

The main process save some of its state to a file on exiting, and
every so often (to protect against abnormal termination). This is done
simple by using the standard shelve module to pickle to a file. There
is a separate thread for the periodic saving - code that changes data
which is to be saved sets an event that the thread examines. The code
for this is in the module persist_.

.. _persist: ./api/persist-module.html


Indexing
========

In order to build Xapian databases from the files specified by a
document collection Flax has a process that runs separately from the
main web server. This has some advantages:

  * Badly behaved document filters invoked by the indexing process
    need not adversely affect the running of the main web server.

  * The indexer could run on a separate machine from the web server if
    desired to improve performance (this is not possible at the
    moment, but could be achieved with small code changed).

  * On multi-core processors the indexing process can run on a
    different core from the web service process. (In practice it
    appears that processes all, by default, run on the same CPU on
    Windows at least, so far no testing has been carried out on
    multicore machines running other OSs.)

This is no long term state held in the indexer, so that at worst the
current indexing process can be forcibly terminated and
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
simultaneous indexing, which might improve performance, especially on
multi-core processors, or if we allowed for indexing processes to run
on separate machines.

.. _IndexServer: ./api/indexserver.indexer.IndexServer-class.html
.. _IndexProcess: ./api/indexserver.indexer.IndexServer-class.html


The actual indexing involves making calls on Xapian_ (via Xappy_) to
make (or update) a database for the collection. The document
collection itself determines which files should be considered for
indexing, and for each file type there is a filter__ that extracts the
text content of the file. In the current implementation the file type
to filter mapping is fixed (for each operating system) but in the
future we plan to allow this mapping to be configured.

The type of the file is currently determined purely by examining the
file extension, and as mentioned above, each file type maps to a
specific filter. This has some limitations and will be addressed
presently. See the `wiki page`_ on the subject for more discussion.


.. __: Filters_
.. _`wiki page`: http://code.google.com/p/flaxcode/wiki/FileTypeRepresentation


Filters
~~~~~~~

A filter is a python callable (a function or an object that implements
``__call__``) that takes a file name and returns an iterator that
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

title
    Ideally there should be exactly one block for this field. This is
    rendered in search results so that users have an idea what the
    document might be. If the filter does not yield a block for title
    then some other information relating to the file (e.g. the file
    name, but this might change) will be used for this purpose.

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
    we make use of mime types.

mimetype
    The mime type of the data. (Not currently used, but reserved for
    future use.)

uri
   URI for the file (not currently used, but reserved for future use).

nametext
   Text extracted from the filename.  Currently, this is just the
   base name of the file, but later we may want to perform various word
   splitting algorithms, and use other parts of the path.

mtime
   The time at which the file was last modified (note: this is not the
   time when it was last indexed), as returned by the standard python
   function ``os.path.getmtime``.

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
messages, it would be nice to separate out internal field names from
external field names.  This would mean that, even if a filter emitted
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
hard coded, so the only way to change the actual filter that gets used
for a particular file is to change the code. On windows we use the
`IFilter filter`_ wrapped up as a `Remote Filter`_ for all file
types. In future we plan to include a configuration mechanism for the
file type (more generally the mime type of the data) to filter
mapping.


For version 1.0 we intend to support at least the following document
formats on Windows:


  * Plain text.
  * HTML.
  * MS Word.
  * MS Excel.
  * MS Power Point.
  * PDF.


It is possible to do this on Windows with a single filter that hooks
into the Windows Indexing Service infrastructure.


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
is possible to directly load the DLLs, but we do not need to do so now
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
to particular Xapian fields.

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
this API some of this infrastructure

.. _samples: http://msdn2.microsoft.com/en-us/library/ms689723.aspx

IFilter filter
~~~~~~~~~~~~~~


The current `IFilter filter`_ started out as a modified version of the
an example_ of using IFilters via COM in the `Python Windows
extensions`_.

.. _example: http://pywin32.cvs.sourceforge.net/pywin32/pywin32/com/win32comext/ifilter/demo/filterDemo.py?view=markup
.. _`IFilter filter`: ./api/indexserver.w32com_ifilter-module.html#ifilter_filter

This works reasonably well, although we seem to get quite a few
exceptions with PDF files for reasons that are not entirely clear.


Simple Text Filter
~~~~~~~~~~~~~~~~~~

For text documents, for testing, and for non-Windows platforms it is
convenient to have a simple filter for text files. This has been
implemented_.

.. _implemented: ./api/indexserver.simple_text_filter-module.html#simple_text_filter


HtmltoText Filter
~~~~~~~~~~~~~~~~~


The Xapian HTML parser has been split off and packaged separately as the
htmltotext_ package. This is used by the html_filter_.

.. _htmltotext: http://pypi.python.org/pypi/htmltotext/0.6
.. _html_filter: ./api/indexserver.htmltotext_filter-module.html#html_filter


PyPdf Filter
~~~~~~~~~~~~

Here_ is a simple filter using PyPdf_, but in practice the current
version throws rather too many exceptions to be generally useful.

.. _Here: ./api/indexserver.pypdf_filter-module.html#pdf_filter
.. _PyPdf: http://pybrary.net/pyPdf/

Remote Filter
~~~~~~~~~~~~~

The instances of the class RemoteFilterRunner run a particular filter
(supplied at initialisation time) in a separate process. Exceptions
get passed back to the main process, and there is a timeout (which
default to 30 seconds) which is the maximum time for which the remote
filter is permitted to finish filtering. If an exception is raised, or
the timeout reached then the remote process is killed and a new one is
started.

There are some costs which we could perhaps address at some point. The
remote process waits until the filtering of a document has finished
before sending all the block back in one go. It could perhaps send
blocks back as they become available. This might be preferable, but
could also lead to more time spent context switching. We could also
arrange to use some shared memory for the inter-process communication
which would remove some copying overheads.

The design is partly indented to accommodate running the remote filter
on a different machine. Although this is not possible currently it
would be straight forward to modify things to allow such.


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


Web User Interface
==================

The classes in the module cpserver_ provide implement the
functionality that is exposed via HTTP. The rendering of web pages is
achieved by making calls on into the templates_ module, which in turn
uses the HTMLTemplates in the templates sub-directory. These templates
also make some use of the images, css and javascript that lives under
the static sub-directory.


The main class in cpserver are Top_ and Admin_, providing respectively
the functionality available to end users and to administrators. The
search and advanced search pages are essentially the same for both
classes of user and these are implemented in the SearchForm_ class.

.. _cpserver: ./api/cpserver_module.html
.. _templates: ./api/templates_module.html
.. _Top: ./api/cpserver.Top-class.html
.. _Admin: ./api/cpserver.Admin-class.html
.. _SearchForm: ./api/cpserver.SearchForm-class.html


The look and feel of the web UI can be changed by editing the
templates and/or the css. Take care not to change the HTMLTemplate_
structure of the pages (given by the 'node="con:...' and
...'node="rep:...') attributes of elements in the templates - unless
...you change the code in the templates_ module correspondingly.

Note that each template has a "body" container - that is an element
with the attribute "con:body", this is used to provide the main
content and should not be removed. Some templates also have a "title"
container, this used to provide the title for the page. Finally some
templates have a separate "heads" container. This contains material
that will be inserted into the "head" element of the resulting web
page and is typically used for (references to) javascript or css
specific to the page.

Pages may be rendered either as user pages, or admin pages. In the
former case the rendered page uses content from the user_banner
template to provide features common to the user pages, and the
admin_banner template plays a similar role for the admin pages.

The template flax is a skeleton providing the content common across
all the web pages served.

The remaining templates provide the main content of each of the web
pages served to users and are described briefly below.

about.html 
    This is used to provide the about pages served from "/about" and
    "/admin/about" and is all static content.

collection_detail.html 
    This is the admin page for viewing and editing collections served
    from "/admin/collections/new" and "/admin/collections/foo/view"
    for each collection "foo".

collections.html
    The admin page listing all collections and allowing control of
    indexing and navigation to the individual collection detail
    pages. This is served from "/admin/collections".

options.html
    The setting pages available via "/admin/options".

search.html 
    The search and search results pages (for both admin and regular
    users).


Running as a Windows Service.
=============================

When running as a Windows service there are a couple of points to
note:

  - stderr and stdout are not proper file handles (this is true for
    any non-console windows application), so it's important that
    things don't get written on them. We try to ensure that everything
    goes through the logging system.

  - The protocols for interacting with the service infrastracture does
    not appear to be properly documented anywhere. Please let us know
    if you know of a *definitive* description.

  - It appears that sys.exitfunc is not called as part of the shutdown
    protocol, so anything that is registered via the atexit module
    does not run. We know that at least the third party processing
    module and the standard logging module use atexit to do clean
    up. We therefore have to manage (some) of these things in our own
    code.


Lifecycle of an issue
=====================

Issues in our tracker have several states (stored in the "Status" field) - the
tracker doesn't enforce how we use them very well, but here's how it should
work.

New issues
--------

A new issue should usually be given a status of "New".  This means that no
technical person has yet investigated it; we don't know whether it's a genuine
issue yet at all.  A new issue should also usually be assigned to "flaxdevs" -
indicating that no specific person has taken responsibility for it yet.

Accepting issues
----------------

Whenever a technical developer has a moment to check the issue tracker, he
should investigate the issues marked as "New", and accept or discard them.  At
this stage, the following actions are appropriate:

 - If a "New" issue looks like a plausible issue, and there are no obvious
   duplicate reports for it, the status should be changed to "Accepted".

 - If there's a duplicate for the issue, it should be marked as "Duplicate",
   and a comment added to say what issue it's a duplicate of.  The original
   issue (ie, the issue which has been duplicated) should be updated with any
   additional information contained in the new issue.

 - If the issue is nonsensical, or due to a misconception, the issue should be
   marked as "Invalid", with a comment added to say why it makes no sense.

 - If the issue may be a valid problem, but there's insufficient detail to know
   whether it is, or no clear way to fix it, the issue should be marked as
   "Clarify".  This can be thought of as a call to other developers to help
   discuss the issue.

 - If the issue is a valid problem, but we have no intention of fixing it (eg,
   it's outside the scope of the project), it should be marked as "WontFix",
   with a comment explaining why we're not going to fix it.

 - If the issue has already been addressed, it should be marked as "Fixed",
   with a comment saying in which version of the software (possibly an SVN
   revision) it was addressed.

 - Otherwise, the issue should be marked as "Accepted".  If there is an obvious
   developer who should fix it, change the assignment to him at that point.
   Otherwise, leave it as "flaxdevs".

The following search will display all issues marked as New::

 http://code.google.com/p/flaxcode/issues/list?can=1&q=status%3ANew&colspec=ID+Type+Status+Priority+Milestone+Owner+Summary&cells=tiles

Fixing issues
-------------

When a developer starts work on an issue, he should ensure that the issue is
assigned to himself, and mark the status of the issue as "Started".  This
avoids duplicating effort by having two developers working on the same thing at
once.

When an issue has been fixed, the developer who fixed it should change the
status from "Assigned" to "Fixed", and add a comment to the issue saying how
it's been fixed, and what revision of the code the issue was fixed in.

Verifying issues
----------------

Periodically (and certainly before every release) other developers should go
through the list of fixed issues, and verify that the fix has worked for them -
this ensures that common mistakes (such as missing a file which needs to be
committed) don't go unnoticed, and provides a layer of QA.  When a second
developer (ie, someone other than the developer who originally fixed the issue)
has verified that the issue is fixed for them, the second developer should mark
the issue as "Verified".  (If the issue isn't fixed for the second developer,
he should mark the issue as "Reopened", and give details of the problem they're
now seeing.)  The following search will display all issues marked as Fixed::

 http://code.google.com/p/flaxcode/issues/list?can=1&q=status%3AFixed&colspec=ID+Type+Status+Priority+Milestone+Owner+Summary&cells=tiles

The same developer who fixed an issue should not usually mark the issue as
Verified - and should certainly not do so unless they've checked the issue has
been fixed on a separate machine.

When a release is made, the release manager should go through the list of
issues and mark all Verified issues as "Released".  This should be done whilst
updating the release notes with the details of all the issues fixed in the new
release.


Release checklist
=================

The following list contains all the steps which need to be taken, in this
order, to prepare for a new release of Flax.

One person needs to be nominated for each release as the release maintainer, to
ensure that all the tasks are done, and done in the right order.

 - Ensure that all changes to the source and documentation are committed.

 - Ensure that all issues marked with a milestone tag for the release you're
   about to make are closed, or changed to be for a later milestone (with an
   explanation for why it's okay to let them slip for now).

 - Ensure that all issues which have been fixed during this release have been
   verified: the following URL is useful for getting a list of issues which
   need to be verified::

	http://code.google.com/p/flaxcode/issues/list?can=1&q=status%3AFixed&colspec=ID+Type+Status+Priority+Milestone+Owner+Summary&cells=tiles

 - Test build of packages and documentation from a fresh checkout of SVN:
   IMPORTANT - after this step, we're committed to associating the current
   state of SVN with a release.  If any problems are found with the build of
   packages or documentation, go back and fix them before proceeding.

 - Update (and commit) the NEWS file, to list all significant changes between
   this release and the last one.  This produces the release notes, which users
   can use to decide whether an update to the new version is appropriate for
   them or not.

 - Go through the list of all issues which have been verified, adding a summary
   (and the issue number) of any which are relevant to users to the NEWS file.
   After committing these updates to the NEWS file, mark the issues as
   "Released".  The following URL is useful for getting a list of issues which
   have been verified.

 - Update ChangeLog file in flax, using the "log2cl" script, so that the
   ChangeLog included in the distribution is up-to-date.  To do this, simply
   run "python utils/log2cl.py", and then manually add a changelog entry with a
   comment of the form::

        * ChangeLog: Update for 1.0.0 release.

 - Increase version numbers in src/version.py to the new release number.
   Remember to set _is_release to True there.

 - Edit documentation to update any version numbers and remove any
   'pre-release' notes in them.  Add any new locations in the documentation
   where version numbers are found to the following list so that they won't be
   missed in the next release.
   - TODO - add items to this list as you find them.

 - Tag the release in SVN.  For example, to tag the 1.0.0 release, you would
   run::

        svn copy https://flaxcode.googlecode.com/svn/trunk https://flaxcode.googlecode.com/svn/tags/release1.0.0 -m "Tag 1.0.0 release"

 - Set _is_release to False in src/version.py.  (This ensures that any further
   development done does not result in builds which have the same version
   information as the official release.)

 - Create new build, from the tagged sources, and add to Googlecode downloads.

 - Create new documentation snapshots, from the tagged sources, and put on
   http://flax.co.uk/.

 - Update links on http://flax.co.uk
   - FIXME - put a list of the links which need updating here.

 - Send announcement mail to flax-announce mailing list.

 - Tell anyone else about the release that we feel should know.
