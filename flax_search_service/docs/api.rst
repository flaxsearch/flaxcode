====================================
Flax Indexing/Search Web Service API
====================================

RESTful HTTP. As far as possible, play nicely with browsers and forms, for ease of debugging etc.

Resources and URIs
==================

======================== ==================================== =================================
Resource type            URI                                  Example
======================== ==================================== =================================
Database                 /<db_name>                           /botany
------------------------ ------------------------------------ ---------------------------------
Fields                   /<db_name>/fields/<field_name>       /botany/fields/genus
------------------------ ------------------------------------ ---------------------------------
Groups                   /<db_name>/fields/<group_name>       /botany/groups/taxonomy
------------------------ ------------------------------------ ---------------------------------
Metadata [#chk]_         /<db_name>/meta/<key>                /botany/meta/wombat
------------------------ ------------------------------------ ---------------------------------
DB Configuration         /<db_name>/config/<key>              /botany/config/synchronous
------------------------ ------------------------------------ ---------------------------------
DB Status                /<db_name>/status                    /botany/status
------------------------ ------------------------------------ ---------------------------------
Document                 /<db_name>/docs/<doc_id>             /botany/docs/42 [#docids]_
------------------------ ------------------------------------ ---------------------------------
Document range           /<db_name>/docs/<start_id>-<end_id>  /botany/docs/23-42 [#docid2]_
------------------------ ------------------------------------ ---------------------------------
Document set             /<db_name>/docs/<id1>,<id2>,...      /botany/docs/3,5,7,11 [#docid2]_
------------------------ ------------------------------------ ---------------------------------
Database terms [#terms]_ /<db_name>/terms                     /botany/terms
------------------------ ------------------------------------ ---------------------------------
Document terms           /<db_name>/docs/<doc_id>/terms       /botany/docs/42/terms
------------------------ ------------------------------------ ---------------------------------
Term range                terms/<start_term>-<end_term>       /botany/terms/leaf-
------------------------ ------------------------------------ ---------------------------------
Term match                terms/<prefix>*                     /botany/terms/XF*
------------------------ ------------------------------------ ---------------------------------
Synonyms                 /<db_name>/synonyms/<original>       /botany/synonyms/fungus
------------------------ ------------------------------------ ---------------------------------
Search                   /<db_name>/search/?<query>           /botany/search/?query=xylem
------------------------ ------------------------------------ ---------------------------------
Replay Log               /<db_name>/log                       /botany/log
======================== ==================================== =================================

.. [#chk] Needs more thought.

.. [#docids] Document IDs can be any string, not just numeric.

.. [#docid2] Does this mean that docids can't contain - and , ?

.. [#terms] Is terms exposing too much? But it's good for populating dropdown lists.

FIXME: Add Facets, spelling correction?

FIXME: Xappy has rich query constructors, how do we make them RESTful?

Formats
=======

JSON:

Fields
------

Each field is defined as a JSON object with the following items (most of which are optional)::

  {
    "field_name":       # field name (required)
    "type":             # One of "text", "date", "geo", "float" (default=text)
    "store":            # boolean (default=false), whether to store in document data
    "spelling_source":  # boolean (default=true), whether to use for building the spelling dictionary
                        # Note - currently, only used if the field is indexed as freetext. FIXME?
    "collapsible":      # boolean (default=false), whether to use for collapsing
    "sortable":         # boolean (default=false), whether to allow sorting on the field
    "range_searchable": # boolean (default=false), whether to allow range searches on the field
    "document_weight':  # boolean (default=false), whether the field value can be used for document weighting
    "noindex":          # boolean (default=false), if true, don't index, but still support above options.
    "freetext": {       # If present (even if empty), or if field type is 'text' 
                        # and no other text indexing option (eg, 'exacttext' or 'noindex') is 
                        # specified, field is indexed for free text searching
        "language":                  # string (2 letter ISO lang code) (default None) - if missing, use 
                                     # database default (FIXME - need to be able to set this).
        "term_frequency_multiplier": # int (default 1) - must be positive or zero - 
                                     # multiplier for term frequency, increases term frequency by the 
                                     # given multipler to increase its weighting
        "enable_phrase_search":      # boolean (default True) - whether to allow phrase searches on this field
     },
     "exacttext":       # boolean. If true, search is indexed for exact text searching
                        # Note - only one of "freetext" and "exact" may be supplied

     "geo": {           # If present (even if empty), or if field type is 'geo' and 'noindex' is not specified,
                        # coordinates are stored such that searches can be ordered by distance from a point.
          "enable_bounding_box_search":  # boolean (default=true) - if true, index such that searches for all 
                                         # items within a bounding box can be retrieved.
          "enable_range_search':  # boolean (default=true) - if true, index such that searches can be 
                                  # restricted to all items within a range (ie, great circle distance) of a point.
      }
  }

Document
--------

Documents are represented as JSON objects where the keys are field names. Each key may have a single string value, or an array of several strings, e.g.::

  { 
    "_doc_id": "sm01",           # optional document ID
    "title": "Slime Molds",
    "category": ["Protista", "Amoeboids", "Fungi"],
    "text": "Slime molds have been found all over the world and feed on 
             microorganisms that live in any type of dead plant material..."
  }

MSet
----

MSets are represented by JSON objects providing match information (see
[http://xappy.org/docs/0.5/api/xappy.searchconnection.SearchResults-class.html SearchResults Properties])
and a list of results. Selected field data can be returned with each hit as a document-like object (see searching below). e.g.::

  {
    "matches_estimated": 234,
    "estimate_is_exact": false,
    "startrank": 10,
    "endrank": 19,
    ...
    "results": [
        { 
          "rank": 10, 
          "weight": 7.23, 
          "percent": 78, 
          "data": { "title": "Physarum Polycephalum", "category": ["Mycetozoa", "Amoebozoa"] }
          "summary": "P. polycephalum is typically yellow in color, and eats fungal spores, 
                      bacteria, and other microbes..."
        }
        ...
    ]
  }

As shown above, a contextual summary can also be returned with each hit (see searching).

POST data
=========

Sent as type ``application/json`` or as ``json`` field in form data. All POST requests must send a JSON object, even if just an empty array or ``true``. The value ``null`` on its own is used to indicate deletion of a resource.

Return Values
=============

Error/success indicated by HTTP response code. Optional JSON body.

Database Methods
================

create database
---------------

e.g.::

    POST /<db_name>
    true

delete database
---------------

e.g.::

    DELETE /<db_name>

get database info
-----------------

e.g.::

    GET /<db_name>

    returns { 'doccount': doccount, 'created': created_date, 'last_modified': last_modified_date }

Field Methods FIXME
===================

set field
---------

A field is created by posting a field description object (see above) to the field resource:

e.g.::

    POST /<db_name>/fields/<field_name>
    {field description object}

This only needs to be done when a database is first created.

get field
---------

e.g.::

    GET /<db_name>/fields/<field_name>
    {field description object}

delete field
------------

e.g.::

    DELETE /<db_name>/fields/<field_name>

get list of field names
-----------------------

e.g.::

    GET /<db_name>/fields

    returns [fieldname_1, fieldname_2, ...]


Group Methods
=============

Groups are provided to make it possible to do efficient searches over two or
more fields. Internally, these fields will be indexed with a single prefix, so
the group can be treated as a single field for searching.  Groups can either
contain ``freetext`` or ``exacttext`` fields, but not both.

create a group
--------------

e.g.::

    POST /<db_name>/groups/<group_name>
    [array of field names]

delete a group
--------------

e.g.::

    DELETE /<db_name>/groups/<group_name>

get fields in a group
---------------------

e.g.::

    GET /<db_name>/groups/<group_name>

    returns [array of field names]

get list of groups
------------------

e.g.::

    GET /<db_name>/groups

    returns [array of group names]

Metadata Methods
================

Document Methods
================

add new document
----------------

e.g.::

    POST /<db_name>/docs/[<doc_id>]
    [document data]

``<doc_id>`` optional. Will create new document, or return error if document id already exists in DB.

returns doc_id (automatically allocated if not specified).

add/replace document
--------------------

e.g.::

    PUT /<db_name>/docs/<doc_id>
    [document data]

Will create new document, or overwrite existing doc.

returns doc_id (in Location: header?)

delete document(s)
------------------

e.g.::

    DELETE /<db_name>/docs/<doc_id>|<doc_range>|<doc_set>

    Transactional; either all documents deleted without error, or none (but what errors could there be?)

get document(s)
---------------

e.g.::

    GET /<db_name>/docs/<doc_id>|<doc_range>|<doc_set>

    returns {document} or [document list]


Multiple document transactions
==============================

Client-managed transactions
---------------------------

The single document operations listed above are committed immediately, so that
they are visible to searches. This is extremely inefficient for adding or
updating a large number of documents, but the Xapian transaction API does not
translate easily to a RESTful approach.

One solution is to allow POST and PUT to supply multiple documents, where the
document ID of each is included with the document data. The POST variant will
not overwrite existing documents, the PUT command will. A Xapian transaction is
started for the first document in the stream, and is committed at the end of
the stream. If an error occurs, the entire stream is aborted.

Since there may be very many documents in a transaction (10,000 is typical), we
do not want to have to store the whole list in memory on the client or the
server. Therefore we should use chunked encoding, and the server should read
docs from the open stream and add them as soon as they are available.

Client-managed transactions are not ideal for all applications, and so this
will have a lower priority than:

Server-managed transactions
---------------------------

This approach is not strictly RESTful but is pragmatic for most real-world
applications. The database can be set to asynchronous mode by setting the DB
configuration parameter ``synchronous`` to ``false`` (perhaps this should be
the default?)  When this is true, documents added to the database will not
necessarily be searchable immediately, but will be queued until the server
decides to add and commit them. This means that if there is an error adding
documents, the client will not be informed synchronously (however, the
documents *will* be validated synchronously as usual, so this is unlikely
to be a problem). 

Setting the ``synchronous`` flag to ``true`` will commit any pending
transactions as a side-effect, so the client could use this as a sort of sloppy
transactional control. 
 
Term Methods
============

Synonym Methods
===============

Search Methods
==============

The complicated stuff!

Defaults
--------

 * config file

