====================================
Flax Indexing/Search Web Service API
====================================

This is the API documentation for the Flax indexing and search web service.
The API is mostly RESTful HTTP, with a few necessary compromises.

Compromises
-----------

Successful requests always return a 200 status code.  201 is not used as a
response status code, even where it would be the most appropriate status code
to return, because some clients (specifically, a PHP client we experimented
with) interpret the Location header in such a response as a redirect.

Resources and URIs
==================

Currently Implemented
---------------------

======================== ================================================== =================================
Resource type            URI                                                Example
======================== ================================================== =================================
Server info              /                                                  /
------------------------ -------------------------------------------------- ---------------------------------
List of databases        /<ver>/dbs                                         /dbs
------------------------ -------------------------------------------------- ---------------------------------
Database                 /<ver>/dbs/<db_name>                               /botany
------------------------ -------------------------------------------------- ---------------------------------
Schema                   /<ver>/dbs/<db_name>/schema                        /botany/schema
------------------------ -------------------------------------------------- ---------------------------------
Default language         /<ver>/dbs/<db_name>/schema/language               /botany/schema/language
------------------------ -------------------------------------------------- ---------------------------------
Fields                   /<ver>/dbs/<db_name>/schema/fields/<field_name>    /botany/schema/fields/genus
------------------------ -------------------------------------------------- ---------------------------------
Groups                   /<ver>/dbs/<db_name>/schema/groups/<group_name>    /botany/schema/groups/taxonomy
------------------------ -------------------------------------------------- ---------------------------------
Metadata                 /<ver>/dbs/<db_name>/meta/<key>                    /botany/meta/wombat
------------------------ -------------------------------------------------- ---------------------------------
DB Configuration         /<ver>/dbs/<db_name>/config/<key>                  /botany/config/synchronous
------------------------ -------------------------------------------------- ---------------------------------
DB Status                /<ver>/dbs/<db_name>/status                        /botany/status
------------------------ -------------------------------------------------- ---------------------------------
Document                 /<ver>/dbs/<db_name>/docs/<doc_id>                 /botany/docs/42 [#docids]_
------------------------ -------------------------------------------------- ---------------------------------
Document range           /<ver>/dbs/<db_name>/docs/<start_id>-<end_id>      /botany/docs/23-42 [#docids]_
------------------------ -------------------------------------------------- ---------------------------------
Document set             /<ver>/dbs/<db_name>/docs/<id1>,<id2>,...          /botany/docs/3,5,7,11 [#docids]_
------------------------ -------------------------------------------------- ---------------------------------
Database terms [#terms]_ /<ver>/dbs/<db_name>/terms                         /botany/terms
------------------------ -------------------------------------------------- ---------------------------------
Document terms           /<ver>/dbs/<db_name>/docs/<doc_id>/terms           /botany/docs/42/terms
------------------------ -------------------------------------------------- ---------------------------------
Term range                terms/<start_term>-<end_term>                     /botany/terms/leaf-
------------------------ -------------------------------------------------- ---------------------------------
Term match                terms/<prefix>*                                   /botany/terms/XF*
------------------------ -------------------------------------------------- ---------------------------------
Synonyms                 /<ver>/dbs/<db_name>/synonyms/<original>           /botany/synonyms/fungus
------------------------ -------------------------------------------------- ---------------------------------
Search                   /<ver>/dbs/<db_name>/search/?<query>               /botany/search/?query=xylem
------------------------ -------------------------------------------------- ---------------------------------
Replay Log               /<ver>/dbs/<db_name>/log                           /botany/log
======================== ================================================== =================================

Not Currently Implemented
-------------------------

======================== ================================================== =================================
Resource type            URI                                                Example
======================== ================================================== =================================


======================== ================================================== =================================


.. [#docids] Document IDs can be any string, not just numeric.  However, note that they must be escaped as described below.

.. [#terms] Is terms exposing too much? But it's good for populating dropdown lists.

TODO: Add support for facets, spelling correction.

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

Each field is defined as a JSON object with the following items (most of which
are optional)::

  {
    "type":             # One of "text", "date", "geo", "float" (default=text)
    "store":            # boolean (default=false), whether to store in document data

    "spelling_source":  # boolean (default=true), whether to use for building the spelling dictionary
    			# This may only be specified for fields of type "text".
                        # Note - currently, only used if the field is indexed as freetext.

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

Documents are represented as JSON objects where the keys are field names. Each
key may have a single string value, or an array of several strings, e.g.::

  { 
    "title": "Slime Molds",
    "category": ["Protista", "Amoeboids", "Fungi"],
    "text": "Slime molds have been found all over the world and feed on 
             microorganisms that live in any type of dead plant material..."
  }

Result set
----------

Result sets are represented by JSON objects providing match information and a
list of results. e.g.::

  {
    "matches_estimated": 234,
    "estimate_is_exact": false,
    "start_rank": 10,
    "end_rank": 20,
    ...
    "results": [
        { 
          "docid": 123,
          "rank": 10, 
          "weight": 7.23, 
          "db": "http://localhost:8080/dbs/foo",
          "data": { "title": ["Physarum Polycephalum"], "category": ["Mycetozoa", "Amoebozoa"] }
          "summary": "P. polycephalum is typically yellow in color, and eats fungal spores, 
                      bacteria, and other microbes..."
        }
        ...
    ]
  }

The fields defined in a result set are as follows.  Note that all fields are
compulsory (ie, clients can rely on them being present), except where marked
with "optional":

 - `matches_estimated`: (integer) An estimate for the number of matching
   results.
 - `matches_lower_bound`: (integer) A lower bound on the number of matching
   results.
 - `matches_upper_bound`: (integer) An upper bound on the number of matching
   results.
 - `matches_human_readable_estimate`: (integer) A human readable estimate of
   the number of results.  This will always lie within the bounds returned, but
   will be rounded to an appropriate accuracy level within these bounds.
 - `estimate_is_exact`: (bool) A boolean, indicating whether the estimate is
   exact.  If true, any of `matches_lower_bound`, `matches_upper_bound`,
   `matches_human_readable_estimate` which are present will be equal to the
   value for `matches_estimated`.
 - `more_matches`: (bool) True if there definitely are further results matching
   the search after this.  False if there definitely aren't.  Implementations
   must always check this.
 - `start_rank`: (integer) The rank of the first result in `results`.
 - `end_rank`: (integer) The rank of the first result after the end of
   `results`.  Note that this is not the rank of the last result in `results`.
 - `results`: (list) A list of dictionaries, one for each result, in increasing
   order of rank.  Each dictionary may have the following members:

   - `rank`: (integer) The rank of the result, where the top result has rank 0.
   - `db`: (string) The base URI of the database which this result came from.
   - `docid`: (string) The ID of the document which this result is for.
   - `weight`: (float, optional) The weight assigned to the result.  Must be
     positive; if absent, assume this is 0.
   - `data`: (dict, optional) The document data.  This is the same format of
     data as is returned by accessing the document directly, but that some
     fields may have been filtered out due to options passed along with the
     search request.
   - `summary`: (dict, optional) A summary of the document data.  The summary
     is field specific, and contains data in the same format as normal document
     data.  Summarisation markup may have been inserted in the data, according
     to options passed along with the search request.

Note that rank here is not defined in the same way as `startIndex` in the
opensearch specification; rank starts at 0, whereas `startIndex` starts at 1.
If implementing an opensearch interface, `matches_human_readable_estimate` is
probably the best value to use for the `totalResults` return value.

As shown above, a contextual summary can also be returned with each hit (see
searching).

POST/PUT data
=============

Data supplied along with a POST or PUT request to many of the resources may
often need to be sent as JSON encoded data.  In this situation, there are two
ways to send it:

 - Send the request body as type ``application/json``.
 - Send the request body as form-encoded data, containing a ``json`` field
   containing the JSON encoded data.

Note that, due to limits on URI lengths supported for GET requests, the API
sometimes allows a POST request (with a large request body) to be made where a
GET request would be more appropriate.

Return Values
=============

An request which attempts to access a resource which is not found will return a
404 error.

Most other errors will be returned as a 400 error, with a JSON body indicating
the details of the error.  FIXME - currently, the body isn't JSON.

Unanticipated internal errors will result in a error in the 500 series, with a
human-readable body indicating some details of the error which occurred.  A
traceback will generally be included in the log in this situation, too.

Currently, all successful requests will result in a 200 status code.  Sometimes
it would be more appropriate to return a 201 or 202 status code, but we have
experienced problems with clients following the associated "Location" headers
as if they were redirects, so for now we're sticking to 200 status codes.

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

If the database is sucessfully created, this will return a 200 response and true body.

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

    GET /dbs/<db_name>

    returns { 'doccount': doccount, 'created': created_date, 'last_modified': last_modified_date }

Field Methods FIXME
===================

set field
---------

A field is created by posting a field description object (see above) to the field resource:

e.g.::

    POST /dbs/<db_name>/fields/<field_name>
    {field description object}

This only needs to be done when a database is first created.

get field
---------

e.g.::

    GET /dbs/<db_name>/fields/<field_name>
    {field description object}

delete field
------------

e.g.::

    DELETE /dbs/<db_name>/fields/<field_name>

get list of field names
-----------------------

e.g.::

    GET /dbs/<db_name>/fields

    returns [fieldname_1, fieldname_2, ...]


Group Methods
=============

Groups are provided to make it possible to do efficient searches over two or
more fields. Internally, a combined index of instances of these fields will be
created, and these combined indexes will be used whenever the fields in the
group are used for searching.

Groups can either contain a set of ``freetext`` fields, or a set of
``exacttext`` fields, but not a mixture of the two.

create or modify a group
------------------------

Method: PUT
Path: /dbs/<db_name>/schema/groups/<group_name>
Body: a JSON list of field names.

Note that this replaces any existing settings for a group of the given name.

e.g.::

    PUT /dbs/<db_name>/schema/groups/<group_name>
    ["field1", "field2"]

delete a group
--------------

e.g.::

    DELETE /dbs/<db_name>/schema/groups/<group_name>

get fields in a group
---------------------

e.g.::

    GET /dbs/<db_name>/schema/groups/<group_name>

    returns [array of field names]

get list of groups
------------------

e.g.::

    GET /dbs/<db_name>/schema/groups

    returns [array of group names]

Metadata Methods
================

Abitrary metadata may be stored in the database.  This is essentially just a
key-value store.

FIXME - this part of the API needs more design work::

 - should there be a method for getting all the keys in the metadata?
 - or should there be a method for getting all  the key-value pairs?
 - should we be using JSON encoded values for the get and set methods, or just
   raw data (as application/octet, perhaps)?

set metadata key
----------------

Method: PUT
Path: /dbs/<db_name>/meta/<key>
Body: a JSON string containing the value to store.
Response: 200 if successful.

e.g.::

    PUT /dbs/foo/meta/name
    "richard"

get metadata key
----------------

Method: GET
Path: /dbs/<db_name>/meta/<key>

Response: a JSON string containing the value stored.

e.g.::

    GET /dbs/foo/meta/name

    returns: "richard"

Document Methods
================

add/replace document
--------------------

e.g.::

    POST /<db_name>/docs/[<doc_id>]
    [document data]

``<doc_id>`` optional. Will create new document, or overwrite existing doc.

returns true (FIXME return doc_id? Might need to create UUID.)

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

search/simple
-------------

FIXME - document; just accepts start and end ranks, and a flat query string
which is interpreted.

search/json
-----------

[RJB note: FIXME - this resource name is far from ideal - it describes a
transfer format, not the purpose of the search.  How about "search/structured"?

While this search structure is useful, it's not particularly general. Also, it
doesn't seem to require JSON, to me - the functionality exposed here could be
provided just by using standard querystring parameter encoding (the
`query_fields` and filters would have the field names appended to the parameter
names, so would become parameters like: `query_field_title`).

[TM note: agreed, this is basically a quick hack to get things to a point where
they can be realistically tested. You mentioned you had some new ideas for "search
templates", so I was waiting to discuss them before finalising an interface.]

Where we _do_ need JSON is to support something like a fully heirarchical tree
of objects expressed in JSON.

For example::

  { 'op': 'AND',
    'subqs': [
      { 'op': 'parse',
        'text': 'hippie zombie',
      },
      { 'op': 'fields',
        'fields': ['title', 'text'],
        'value': 'land down under',
      }
    ]
  }

where this example would parse the text "hippie zombie", and AND the resulting
query with a query in the fields "title" and "text" for "land down under".

end RJB note]

Search params are supplied as a POSTed JSON object, e.g.::

    {
        "startIndex":       1,
        "count":            10,
        "query_all":        "hippie zombie",
        "query_any":        "brussels muscles",
        "query_none":       "spider",
        "query_phrase":     "vegemite sandwich",
        "query_fields":     { "title":  "land down under" }
        "filters":          { "genre":  "pop",
                              "era":    "80s" }
    }

(query_fields and filters are essentially the same, except for using OP_AND and 
OP_FILTER respectively).


Defaults
--------

 * config file

