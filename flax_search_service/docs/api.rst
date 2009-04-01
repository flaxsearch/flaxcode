====================================
Flax Indexing/Search Web Service API
====================================

RESTful HTTP. As far as possible, play nicely with browsers and forms, for ease of debugging etc.

Resources and URIs
==================

======================== ============================================== =================================
Resource type            URI                                            Example
======================== ============================================== =================================
Server info              /                                              /
------------------------ ---------------------------------------------- ---------------------------------
List of databases        /dbs                                           /dbs
------------------------ ---------------------------------------------- ---------------------------------
Database                 /dbs/<db_name>                                 /botany
------------------------ ---------------------------------------------- ---------------------------------
Schema                   /dbs/<db_name>/schema                          /botany/schema
------------------------ ---------------------------------------------- ---------------------------------
Default language         /dbs/<db_name>/schema/language                 /botany/schema/language
------------------------ ---------------------------------------------- ---------------------------------
Fields                   /dbs/<db_name>/schema/fields/<field_name>      /botany/schema/fields/genus
------------------------ ---------------------------------------------- ---------------------------------
Groups                   /dbs/<db_name>/schema/groups/<group_name>      /botany/schema/groups/taxonomy
------------------------ ---------------------------------------------- ---------------------------------
Metadata [#chk]_         /dbs/<db_name>/meta/<key>                      /botany/meta/wombat
------------------------ ---------------------------------------------- ---------------------------------
DB Configuration         /dbs/<db_name>/config/<key>                    /botany/config/synchronous
------------------------ ---------------------------------------------- ---------------------------------
DB Status                /dbs/<db_name>/status                          /botany/status
------------------------ ---------------------------------------------- ---------------------------------
Document                 /dbs/<db_name>/docs/<doc_id>                   /botany/docs/42 [#docids]_
------------------------ ---------------------------------------------- ---------------------------------
Document range           /dbs/<db_name>/docs/<start_id>-<end_id>        /botany/docs/23-42 [#docid2]_
------------------------ ---------------------------------------------- ---------------------------------
Document set             /dbs/<db_name>/docs/<id1>,<id2>,...            /botany/docs/3,5,7,11 [#docid2]_
------------------------ ---------------------------------------------- ---------------------------------
Database terms [#terms]_ /dbs/<db_name>/terms                           /botany/terms
------------------------ ---------------------------------------------- ---------------------------------
Document terms           /dbs/<db_name>/docs/<doc_id>/terms             /botany/docs/42/terms
------------------------ ---------------------------------------------- ---------------------------------
Term range                terms/<start_term>-<end_term>                 /botany/terms/leaf-
------------------------ ---------------------------------------------- ---------------------------------
Term match                terms/<prefix>*                               /botany/terms/XF*
------------------------ ---------------------------------------------- ---------------------------------
Synonyms                 /dbs/<db_name>/synonyms/<original>             /botany/synonyms/fungus
------------------------ ---------------------------------------------- ---------------------------------
Search                   /dbs/<db_name>/search/?<query>                 /botany/search/?query=xylem
------------------------ ---------------------------------------------- ---------------------------------
Replay Log               /dbs/<db_name>/log                             /botany/log
======================== ============================================== =================================

.. [#chk] Needs more thought.

.. [#docids] Document IDs can be any string, not just numeric.

.. [#docid2] Does this mean that docids can't contain - and , ?

.. [#terms] Is terms exposing too much? But it's good for populating dropdown lists.

TODO: Add Facets, spelling correction.

FIXME: Xappy has rich query constructors, how do we make them RESTful? - we
probably don't; just define a JSON format for representing a query,
heirarchically, as a combination of various subqueries.

Formats
=======

Identifiers
-----------

Database names, field names, group names, metadata keys, and document IDs are
allowed to be any valid unicode string containing at least one character.  When
supplied in URIs, they must be encoded in UTF-8, and any characters other than
the following must be escaped (using % encoding): 'a' to 'z', 'A' to 'Z', '0'
to '9', '.' and '_'.

Note that '-' is not normally escaped in this context (eg, python's
urllib.quote() function does not escape it), but it is necessary to escape it
in document IDs to allow document ID ranges to be specified unambiguously.  For
consistency, we therefore require that '-' is escaped in all identifiers.

Fields
------

Each field is defined as a JSON object with the following items (most of which are optional)::

  {
    "type":             # One of "text", "date", "geo", "float" (default=text)
    "store":            # boolean (default=false), whether to store in document data

    "spelling_source":  # boolean (default=true), whether to use for building the spelling dictionary
                        # Note - currently, only used if the field is indexed as freetext. FIXME?
                        # May only be specified if type == "text".

    "sortable":         # boolean (default=false), whether to allow sorting, collapsing and weighting on the field
                        # Allowed for type == "text", "date", "float" - not for "geo".

    "freetext": {       # If present (even if empty) field is indexed for free text searching
                        # Requires type == "text".
        "language":                  # string (2 letter ISO lang code) (default None) - if missing, use
                                     # database default.
        "term_frequency_multiplier": # int (default 1) - must be positive or zero -
                                     # multiplier for term frequency, increases term frequency by the
                                     # given multipler to increase its weighting
        "enable_phrase_search":      # boolean (default True) - whether to allow phrase searches on this field
     },
     "exacttext":       # boolean. If true, search is indexed for exact text searching
                        # Requires type == "text".
                        # Note - only one of "freetext" and "exact" may be supplied

     "range" {
         # details of the acceleration terms to use for range searches.  May only be specified if type == "float" and sortable == true.
         # FIXME - contents of this hasn't been defined yet - we'll work it out once we have the rest working.
     }

     "geo": {
          # If present (even if empty), coordinates are stored such that searches can be ordered by distance from a point.
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

POST/PUT data
=============

Sent as type ``application/json`` or as ``json`` field in form data.

All POST requests must send a JSON object, even if just an empty array or
``true``.  # FIXME - why?

The value ``null`` on its own is used to indicate deletion of a resource.
# FIXME - is it?  we're probably using the DELETE method instead, actually.

Return Values
=============

Error/success indicated by HTTP response code. Optional JSON body.

Database Methods
================

create database
---------------

Optional parameters:

 - overwrite: If 1, overwrite an existing database.  If 0 or omitted, give an
   error if the database already exists.
 - reopen: If 1, and database exists, do nothing.  If 0 or omitted, give an
   error if the database already exists.

e.g.::

    POST /dbs/<db_name>

If the database is sucessfully created, this will return a 201 response.

delete database
---------------

Optional parameters:

 - allow_missing: If 1, and the database doesn't exist, do nothing.  If 0 or
   omitted, give an error if database doesn't exist.

e.g.::

    DELETE /dbs/<db_name>

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

    Transactional; either all documents deleted without error, or none (but what errors could there be?) - database corruption, out of memory errors, networking errors (when we support multi-database backends), etc.

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

