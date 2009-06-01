=======================
Flax Search Service API
=======================

This is the API documentation for the Flax indexing and search web service (FSS).
The API is mostly RESTful HTTP, with a few necessary compromises.

Compromises
-----------

Successful requests always return a 200 status code.  201 is not used as a
response status code, even where it would be the most appropriate status code
to return, because some clients (specifically, a PHP client we experimented
with) interpret the Location header in such a response as a redirect.


Resources and URIs
==================

API Version
-----------

Apart from the root path which returns server information, all paths are prefixed
with a version code (currently v1). This is so FSS can maintain backwards 
compatibility with existing client code while being able to change the API
design in later versions.

List of Resources
-----------------

======================== ==================================================
Resource type            URI                                               
======================== ==================================================
Server info              /
------------------------ --------------------------------------------------
Set of databases         /v1/dbs                                             
------------------------ --------------------------------------------------  
Database                 /v1/dbs/<db_name>                                  
------------------------ --------------------------------------------------  
Schema                   /v1/dbs/<db_name>/schema                            
------------------------ --------------------------------------------------  
Default language         /v1/dbs/<db_name>/schema/language                   
------------------------ --------------------------------------------------  
Set of fields            /v1/dbs/<db_name>/schema/fields
------------------------ --------------------------------------------------  
Field definition         /v1/dbs/<db_name>/schema/fields/<field_name>       
------------------------ --------------------------------------------------  
Set of documents         /v1/dbs/<db_name>/docs
------------------------ --------------------------------------------------  
Document                 /v1/dbs/<db_name>/docs/<doc_id>  [#docids]_
------------------------ --------------------------------------------------  
Search (Simple)          /v1/dbs/<db_name>/search/simple?<query_str>
------------------------ --------------------------------------------------  
Search (Structured)      /v1/dbs/<db_name>/search/structured?<query_str>
------------------------ --------------------------------------------------  
Search (Similar)         /v1/dbs/<db_name>/search/simple?<query_str>
------------------------ --------------------------------------------------  
Flush control            /v1/dbs/<db_name>/flush
------------------------ --------------------------------------------------  
API Autodocs             /doc
======================== ==================================================  

.. [#docids] Document IDs can be any string, not just numeric.  However, note 
   that they must be escaped as described below.


Data Formats
============

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

Note that rank here is not defined in the same way as `startIndex` in the
opensearch specification; rank starts at 0, whereas `startIndex` starts at 1.
If implementing an opensearch interface, `matches_human_readable_estimate` is
probably the best value to use for the `totalResults` return value.



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


Transactions
============

The REST model is inherently untransactional, however the underlying database
is designed to support transactions. It is not efficient to commit each 
document addition or update to the database immediately (this can slow down
indexing by an order of magnitude if thousands of documents are involved).
Therefore we have a compromise in the design.

Current API
-----------

Transaction support in the current API is primitive, and was implemented quickly
in order to allow testing other other features to get underway. The client code
basically has no control over transactions, other than being able to ensure that
all pending changes have been committed. This is done by POSTING an empty body
(or JSON null or any other object) to the database's /flush resource:

    POST /v1/dbs/<db_name>/flush
    {}

There is no way of explicitly beginning or cancelling a transaction. See 
future.rst for possible future approaches to transactions.


Database Methods
================

create database
---------------

    POST /v1/dbs/<db_name>

Optional parameters:

 - overwrite: If 1, overwrite an existing database.  If 0 or omitted, give an
   error if the database already exists.
 - reopen: If 1, and database exists, do nothing.  If 0 or omitted, give an
   error if the database already exists.


If the database is sucessfully created, this will return a 200 response and true body.

delete database
---------------

    DELETE /v1/dbs/<db_name>

Optional parameters:

 - allow_missing: If 1, and the database doesn't exist, do nothing.  If 0 or
   omitted, give an error if database doesn't exist.

get database info
-----------------

    GET /v1/dbs/<db_name>

returns { 'doccount': doccount, 'created': created_date, 'last_modified': last_modified_date }


Schema Methods
==============

The database schema specifies the types of document fields and how they are
indexed and/or stored.

Set field
---------

    POST /v1/dbs/<db_name>/schema/fields/<field_name>
    {field description object}

A field is created by posting a field description object (see above) to 
the field resource.

Field setup will typically be done when a database is first created, and if 
it is changed after documents have been added, only new documents will be 
affected by the change (unlike a RDBMS).

Get field
---------

    GET /v1/dbs/<db_name>/schema/fields/<field_name>

Returns a field description JSON object.

Delete field
------------

    DELETE /v1/dbs/<db_name>/schema/fields/<field_name>

Get list of field names
-----------------------

    GET /v1/dbs/<db_name>/schema/fields

returns a list of fieldnames, e.g.: ["title", "author", "date", ...]

Set default language
--------------------

    POST /v1/dbs/<db_name>/schema/language?language=<language>

Where language must be specified as a 2 character ISO-639 language code
out of the set (da, nl, en, fi, fr, de, it, no, pt, ru, es, sv). This
will specify the stemming (suffix stripping) algorithm to be employed for
indexing and search. If <language> is the empty string, no stemming
will be used.


Document Methods
================

add/replace document
--------------------

    POST /<db_name>/docs[/<doc_id>]
    {document data}

``<doc_id>`` is optional. If not supplied, FSS will assign a new ID to the document
and add it to the database.
Will create new document, or overwrite existing one.

delete document
---------------

    DELETE /<db_name>/docs/<doc_id>

get document
------------

    GET /<db_name>/docs/<doc_id>

Returns the document as a JSON object.


Search Methods
==============

The API currrently supports three search methods:

Simple search
-------------

    GET /v1/dbs/<db_name>/search/simple?query=<query>

Where <query> contains words to search for in the database (in fact the string is 
passed to the Xapian query parser, so it may also contain operators and quoted
phrases).

This returns a JSON result set object (see above). Documents are ranked in descending
order of relevance, with the top document having rank 0, the second 1, etc.

Optional parameters: 

 - start_rank: The rank of the first document to return in the result set
               (defaults to 0).
 - end_rank: One past the rank of the last document to return (defaults to 10).
 - summary_field: One or more field names to summarise rather than return raw.
 - summary_maxlen: The maximum summary length (per field).
 - highlight_bra: String to insert before a highlighted word.
 - highlight_ket: String to insert after a highlighted word.

These parameters may be used to implement a paging interface.

Structured search
-----------------

    GET /v1/dbs/<db_name>/search/structured?<params>

This includes explicit support for combining different types of query, specified
as the optional parameters:

 - query_all: match must contain all these words
 - query_any: match must contain one or more of these words
 - query_none: match must not contain any of these words

Where words are separated by spaces. Structured search also allows searches to be
filtered by fields which have been indexed with "exacttext". Each filter is supplied
as a parameter with the name "filter" and the value "<fieldname>:<value>"

e.g.: to search for documents containing "foo" and "bar" but not "wombat", filtered
by author and category:

    ?query_all=foo+bar&query_none=wombat&filter=author:smith&filter=category:book

Structured search also accepts the start_rank and end_rank parameters as above.
    
Similarity search
-----------------

    GET /v1/dbs/<db_name>/search/similar?id=<doc_id>

This method finds documents similar to the one specified by <doc_id>, and returns
them ranked in order of similarity. Like the other search methods, it has the
optional parameters start_rank and end_rank.







