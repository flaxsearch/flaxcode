=====================
Flax Basic: Reference
=====================

What is Flax Basic?
===================

System Requirements
===================

Installation and Running
========================
See also the Quick Start document provided with Flax Basic.

Windows
-------

Linux/Unix/MacOS
----------------

Web Proxies
-----------

Administrators
==============

Logging in
----------
The administration interface is accessed through Flax's ``/admin`` URL. For example, if
you are running your browser on the same machine that Flax is running on, enter:

    ``http://localhost:8090/admin``
    
in your browser's address field. If this is a new session, you will then be prompted
to enter the administration username and password.

FIXME picture

Enter ``"admin"`` as the username, and the password you set when installing Flax 
(for instructions on how to change the password, see below.) Flax will then display the
main Collections page. 

Changing the Administration Password
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    1.  **On Windows**
        
        Run the Flax Password utility from the Start menu (FIXME).
        
    2.  **Linux/Unix/MacOS**
    
        First stop the Flax process, if it is running. Then enter the following on the
        command line:  (FIXME)
        
            ``$ python startflax.py -d data --conf-dir=. --set-admin-password``
        
        You will then be prompted to enter and confirm a new password. After entering
        it, restart Flax as ususal.

Collections
-----------
A collection is a specification for a set of documents to index, together with parameters
to control the indexing. A collection may be searched separately or together with other
collections.

Collections are a convenient way to organise your indexes when there are clear differences
in the types of source documents. One example is when you have a set of "reference" 
documents that are rarely updated, and "working" documents which are updated several times
a day. In this case, organising each set as a separate collection allows the indexing to
be scheduled more frequently for the working documents than the reference set, with 
better indexing efficiency.

Collections are also useful when you distinct sets of end users - for example, technical
and marketing staff - who will generally only want to search documents in their own
subject area. This leads to better, faster searches.

Creating a Collection
~~~~~~~~~~~~~~~~~~~~~
When you run Flax for the first time, the Collections list will be empty.

FIXME picture

To create a new collection, click the **Create a new collection** link. This takes you
to the collection details page, with blank fields. The fields are arranged in four sections:

    1.  Document Collection
    
        This section has two fields, *Name* and *Description*. The first is a short name
        which is used by Flax as a label for the collection, and is required. The 
        description is optional, and can be of any length.
    
    2.  Files Specification
    
        This section controls which files will be included in the collection. Currently, 
        Flax can only index files on file systems attached to the computer running Flax,
        including network file systems/shared folders (other access methods will be 
        added in a later release of Flax.)
        
        Each collection requires one or more *Path* fields, which specifies the parent
        directory which will be scanned for files. Subdirectories will also be scanned
        recursively. If you want to specify more than one path, click the *Add another path*
        button. Path fields can be left blank to be omitted from the collection, so 
        long as at least one has a value.
        
        Each *Path* has a corresponding *Mapping* field, which is used to generate URLs
        for search result objects. Files are not served directly through Flax - mostly
        as this could be used to circumvent any access restrictions implemented through
        the file system or other means. Any value in the mapping field will replace the
        path prefix in the generated URL.
        
        Flax is generally intended to work alongside an existing web server, ideally
        using it as a proxy (see above), and using it to serve documents from Flax's
        search results page. For example, using the main web server as a proxy, if
        documents from the folder ``C:\foo\bar\recipes`` is served as the URL 
        ``/main/recipes``, then you should enter:
        
            ``Path:     C:\foo\bar\recipes``
            ``Mapping:  /main/recipes``
            
        If the main web server is not being used as a proxy, you should enter a
        fully-qualified URL which specifies the server, e.g.:
        
            ``Path:     C:\foo\bar\recipes``
            ``Mapping:  http://www.netveggie.foo/main/recipes``
              
        If you are running a browser on the same machine as Flax, you may also specify
        ``file://`` URLs, but this is of limited use, for testing only.
        
        FIXME CP fileserver?
        
        The *Formats* list allows you to choose file types to be included in the index. 
        If you leave all unselected, Flax will index all file types.
        
        Finally, the *Age* field lets you exclude files with a modification time greater
        than the period selected. When re-indexing a collection, any files that now
        exceed the Age field (if set) will be removed.
        
    3.  Indexing Options
    
        Options controlling the way files are indexed. Currently, this is just a language
        selection and a list of *stopwords*.  The latter are words to exclude from the
        index (typically words such as "the", "or", "and" etc which have little to do
        with the topic of a document). There is generally little need to set stopwords
        except when trying to limit index size, so if in doubt, leave this field empty.
        Stopwords, if set, should be separated by spaces.
        
        The *Language* option primarily controls the *stemming*, or suffix-stripping, of
        indexed words. This technique improves searching by normalising inflected forms
        of words, so that, for example, "cycle" would match "cycled", "cycling", "cycles"
        etc. Since this is a language-dependent feature, the main language of a collection
        should be chosen if stemming is to be used.
        
        If you have documents in several different languages, you can either index and
        search them as separate collections, with the language field set accordingly, or
        index them all with language set to *None*, in which case stemming will not be
        performed.
    
    4.  Scheduling
    
        Indexing can be initiated manually (see below) or at automatically at scheduled
        times (the Flax service must be running for this to work.) Scheduling works by
        matching the current time, once per minute, against the scheduling specification
        of a collection (if set). If **all** of the fields (*Minutes*, *Hours*, *Weekdays*,
        *Monthdays* and *Months*) matches the current time then the collection is
        scheduled for indexing. A blank field will never match, ensuring that no scheduled
        indexing will be performed if any field is blank. The "*" wildcard matches any
        value. Otherwise, the scheduler expects a comma-delimeted list of integers.
        
        For example, to schedule reindexing on the hour, every day, enter:
        
            ``Minutes:      0``
            ``Hours:        *``
            ``Weekdays:     *``
            ``Monthdays:    *``
            ``Months:       *``
            
        To reindex at 3.30am every weekday (Mondays are 0, Sundays are 6):

            ``Minutes:      30``
            ``Hours:        3``
            ``Weekdays:     0, 1, 2, 3, 4``
            ``Monthdays:    *``
            ``Months:       *``

After entering details for the new collection, click the *Apply* button at the bottom
of the page. Flax will create the new collection and return you to the Collections list.

Indexing a Collection
~~~~~~~~~~~~~~~~~~~~~
Before searching a collection, it must be *indexed*. This scans all the documents defined
by the collection, extracts text from them, and creates a index on disk for optimised
searching. Flax will only index one collection at a time, as this is the most efficient
use of machine resources. More than one collection may be due for indexing, in which case
they will be indexed in an arbitrary order. This may be controlled, where necessary, with
the manual controls described below.

FIXME indexer running, Start a new one, what happens?

    1.  Unscheduled Indexing
    
        To 
    
    2.  Scheduled Indexing
    3.  Holding Indexing
            
Editing and Deleting a Collection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Searching
---------
See below

Options
-------

Logging
-------

Users
=====

Simple Search
-------------

Advanced Search
---------------

Troubleshooting
===============

