Flax Search Client for PHP: API documentation
=============================================

This document should be used in conjunction with the API documentation for the
Flax Search Service (FSS), which documents data formats amongst other things.


FlaxSearchService class
-----------------------
This class represents a connection to an instance of FSS. To create a connection,
pass the base URL of the FSS instance to the constructor, e.g.:

    $flax = new FlaxSearchService('http://localhost:8080/');

This class currently supports two methods:

    createDatabase($name, $overwrite=false, $reopen=false)
    ------------------------------------------------------
    Create a new database identified by $name, and returns an object representing it. 
    e.g.:

        $db = $flax->createDatabase('news');

    If a database of this name already exists and $overwrite is true, a new empty 
    database will be created, replacing the existing one. If $reopen is true, any 
    existing database will opened instead of creating a new one. If neither parameter 
    is true, and a database already exists with this name, an exception will be thrown.
    
    getDatabase($name)
    ------------------
    Open an existing database named $name, and return an object representing it. If
    no such database exists, throw an error.


Database objects
----------------
Database objects encapsulate most of the API's functionality, with the methods:

    delete()
    --------
    Deletes the database resource referenced by this object.

    getDocCount()
    -------------
    Returns a count of the documents in the database.

    getFieldNames()
    ---------------
    Returns a list of names of fields in this database's schema.

    getField($fieldname)
    --------------------
    Returns an JSON object representing the settings for the named field (see FSS API
    documentation for a description of this data structure). Throws an exception
    if the named field does not exist.

    addField($fieldname, $settings)
    -------------------------------
    Adds a field definition with the specified name and settings, where the latter is
    an instance of FlaxField (see below). Throws an exception if the field already exists.

    replaceField($fieldname, $settings)
    ------------------------------------
    The same as addField(), except that it will overwrite any existing settings
    for the named field.

    deleteField($fieldname)
    -----------------------
    Delete the named field from this database's schema.

    getDocument($docid)
    -------------------
    Returns the document identified by $docid. The document is returned as a JSON object.
    See the FSS API documentation for a description of the data structure.

    addDocument($docdata, $docid=null)
    ----------------------------------
    Adds the document supplied as a JSON object ($docdata) to the database. If $docid
    is supplied, this will be the document's ID (overwriting any existing document with
    this ID). Otherwise a new ID will be generated.

    deleteDocument($docid)
    ----------------------
    Deletes the document identified by $docid from the database.

    commit()
    --------
    This is a temporary method, until the write caching mechanism in the FSS is
    finalised. It causes all document additions and deletions to be committed to
    the database, making them available to searches.

    searchSimple($query, $start_rank=0, $end_rank=10)
    -------------------------------------------------
    Search for the words in $query in the database, and returns matching documents
    as a FlaxSearchResultSet object (see below). $start_rank and $end_rank specify the 
    start and end indexes (zero-based) of the set of documents to return.

    searchStructured($query_all, $query_any, $query_none, $query_phrase,
                     $filters=array(), $start_rank=0, $end_rank=10) 
    --------------------------------------------------------------------
    A more complex search API which can be used (for example) to implement "advanced
    search" GUIs:

    $query_all: All words in this subquery must be matched.
    $query_any: At least one word must be matched.
    $query_none: Exclude documents containing any of these words.
    $query_phrase: Matches an exact phrase.
    $filters: Apply filters to the query, which must match the named fields exactly. 
        Each filter is supplied as a 2-item array (fieldname, value), e.g.:

        $filters = array(array('category', 'sport'), array('source', 'Reuters'));

        If multiple filters are supplied for the same field, they are combined with OR.
        Between fields, filters are combined with AND.


FlaxField classes
-----------------
This is an abstract class, with currently three concrete subclasses:

    FlaxTextField
    -------------
    A text field which is stored, but not indexed. Takes no constructor params.

    FlaxExactTextField class
    ------------------------
    A text field which is indexed as exact text. It may be stored or not.

        __construct($store=false)
        -------------------------
        Constructor for FlaxExactTextField. If $store, the field is stored in the database.

    FlaxFreeTextField class
    ------------------------
    A text field which is indexed as free text. It may be stored or not, and a language
    code may be supplied to control stemming of terms.

        __construct($store=false, $lang=null)
        -------------------------------------
        Constructor for FlaxFreeTextField. If $store, the field is stored in the database.
        If $lang is supplied, terms will be stemmed for this language.


FlaxSearchResultSet class
-------------------------
Search results are returned as instances of this class. It has the public members:

    $matches_estimated: Estimated total number of matches in the database.
    $estimate_is_exact: True iff the estimate is exact.
    $matches_lower_bound: An absolute lower bound on the estimate.
    $matches_upper_bound: An absolute upper bound on the estimate.
    $matches_human_readable_estimate: Get a human readable estimate of the number of 
        matching documents. This consists of the value returned by $matches_estimated,
        rounded to an appropriate number of significant digits.
    $start_rank: The rank (zero-based) of the first item in $results.
    $end_rank: The rank one past the last item in $results.
    $more_matches: True iff there are more matches available after $end_rank;
    $results: An array of FlaxSearchResult objects.

FlaxSearchResult class
----------------------
Represents a single search result, with the public members:

    $docid: The ID of the matching document.
    $rank: Its rank (zero-based), generally in descending order of relevance.
    $weight: The match weight (note that the exact meaning of this value is debatable).
    $db: A URL to the database which provided this result.
    $data: An array containing document data (fields which were stored at index time).


