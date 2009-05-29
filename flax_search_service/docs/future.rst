===================================
Flax Search Service Future Features
===================================

This is where we have moved notes for ideas that haven't made it into
the current release.


Resources planned for implementation
------------------------------------

======================== ==================================================  
Resource type            URI                                                 
======================== ==================================================  
Groups                   /v1/dbs/<db_name>/schema/groups/<group_name>    
------------------------ -------------------------------------------------- 
Metadata                 /v1/dbs/<db_name>/meta/<key>                 
------------------------ -------------------------------------------------- 
DB Configuration         /v1/dbs/<db_name>/config/<key>                 
------------------------ -------------------------------------------------- 
DB Status                /v1/dbs/<db_name>/status                        
------------------------ -------------------------------------------------- 
Replay Log               /v1/dbs/<db_name>/log                           
------------------------ -------------------------------------------------- 
Document range           /v1/dbs/<db_name>/docs/<start_id>-<end_id>          
------------------------ --------------------------------------------------  
Document set             /v1/dbs/<db_name>/docs/<id1>,<id2>,...              
------------------------ --------------------------------------------------  
Database terms [#terms]_ /v1/dbs/<db_name>/terms                             
------------------------ --------------------------------------------------  
Document terms           /v1/dbs/<db_name>/docs/<doc_id>/terms               
------------------------ --------------------------------------------------  
Term range               terms/<start_term>-<end_term>                     
------------------------ --------------------------------------------------  
Term match               terms/<prefix>*                                    
------------------------ --------------------------------------------------  
Synonyms                 /v1/dbs/<db_name>/synonyms/<original>            
======================== ================================================== 

.. [#terms] Is terms exposing too much? But it's good for populating dropdown lists.


TODO: Add support for facets, spelling correction.


Transaction Support
===================

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


Summaries
=========
Extra parameters to support in search methods:

    summary_fields: list of fields (comma-separated) to summarise.
    summary_maxlen: maximum length of summary, per field (default: 500 chars).
    highlight_bra:  opening string for highlighted word (optional).
    highlight_ket:  closing string for highlighted word (optional).

Summaries will NOT be returned separately. Any fields listed in summary_fields will be
summarised and returned -instead- of the raw field data in the "data" array of the search
result.


Group Methods (not yet implemented)
===================================

Groups are provided to make it possible to do efficient searches over two or
more fields. Internally, a combined index of instances of these fields will be
created, and these combined indexes will be used whenever the fields in the
group are used for searching.

Groups can either contain a set of ``freetext`` fields, or a set of
``exacttext`` fields, but not a mixture of the two.

create or modify a group
------------------------

Method: PUT
Path: /v1/dbs/<db_name>/schema/groups/<group_name>
Body: a JSON list of field names.

Note that this replaces any existing settings for a group of the given name.

e.g.::

    PUT /v1/dbs/<db_name>/schema/groups/<group_name>
    ["field1", "field2"]

delete a group
--------------

e.g.::

    DELETE /v1/dbs/<db_name>/schema/groups/<group_name>

get fields in a group
---------------------

e.g.::

    GET /v1/dbs/<db_name>/schema/groups/<group_name>

    returns [array of field names]

get list of groups
------------------

e.g.::

    GET /v1/dbs/<db_name>/schema/groups

    returns [array of group names]


Metadata Methods (not yet implemented)
======================================

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
Path: /v1/dbs/<db_name>/meta/<key>
Body: a JSON string containing the value to store.
Response: 200 if successful.

e.g.::

    PUT /v1/dbs/foo/meta/name
    "richard"

get metadata key
----------------

Method: GET
Path: /v1/dbs/<db_name>/meta/<key>

Response: a JSON string containing the value stored.

e.g.::

    GET /v1/dbs/foo/meta/name

    returns: "richard"


