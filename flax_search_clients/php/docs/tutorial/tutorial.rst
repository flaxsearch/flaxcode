============================================
Flax Search Service Client for PHP: Tutorial
============================================

Introduction
------------

The Flax Search Service Client for PHP (FSSC-PHP) is a library to simplify 
working with the Flax Search Service (FSS) in PHP. This tutorial assumes that
FSS and FSSC-PHP have been installed and tested, and introduces working with
the API through a simple example application. The script is also available 
as tutorial.php in this directory, and can be run with:

    $ php tutorial.php


Basic Concepts
--------------

FSS provides a RESTful Web API for indexing and searching documents. It is
designed to have pluggable back-ends, and currently works with the Xappy/Xapian
search engine. The current pre-alpha release supports basic indexing and search
functions; future releases will add advanced features like facets and image search.

The motivation behind FSS is to provide a state-of-the-art information retrieval
system that can be easily used with a wide variety of platforms and technologies.
Web APIs are inherently agnostic about programming language and system architecture,
and encourage loose coupling, re-use and re-engineering. They also have predictable
scalability and work well with existing firewalls and proxies.

FSS models databases, documents, searches etc as resources which are accessed 
through the standard HTTP methods GET, POST, PUT and DELETE. FSSC-PHP provides a
thin class library to hide the details of the web interface and make writing
applications simpler.


Using FSSC-PHP in PHP applications
----------------------------------

Assuming the flax/ directory containing the FSSC-PHP classes is on the PHP library
path, include the classes in your application with the line:

    require_once('flax/flaxclient.php');

The first step in using FSSC-PHP is to make a connection to a running instance of
FSS. This can be running locally or anywhere on the network or internet. To instantiate
the connection, pass the base URL of the FSS instance to the constructor, e.g.:

    $flax = new FlaxSearchService("http://localhost:8080/");


Creating a new database
-----------------------

To create a new database, use the createDatabase method of the service object, passing
a name for the database, e.g.:

    $db = $flax->createDatabase('my_database');

You can use any characters in a database name, even something like "*&/%$!". If a
database with this name already exists, an exception will be thrown. (This behaviour
can be overridden - see the API documentation.)

If you want to open an existing database, use:

    $db = $flax->getDatabase('my_database');

Most subsequent functionality is handled by these database objects.


Setting up a schema
-------------------

In FSS, documents are made up of named fields. Fields can have different data types,
and can be indexed for different purposes. In this pre-alpha release, only text fields
are supported, and they can be indexed either as "freetext" or as "exacttext". The
former is suitable for blocks of text, and allows the field to be searched for
individual words, phrases, or combinations thereof. "exacttext", on the other hand,
indexes fields as a single exact string, which can only be matched as a whole. This
makes it suitable for document metadata such as author, document type etc. Future
releases of FSS will handle dates, numbers, and more complex types.

A set of field definitions is set up for a whole database, and is known as a schema.
This only needs to be done once after the database is created, and care should be
taken if a schema is altered on a database containing documents, as it may have an
adverse effect on searching existing documents. In general, don't do it!

To add a field definition to a schema, database object provide the addField method,
which takes a fieldname and a field definition. By way of example, let's add a
field to our new database:

    $db->addField('text', array('freetext' => array('language' => 'en'), 
                                'store' => true));

(Field definitions are currently defined as arrays, since these can be easily
serialised to JSON and sent to the FSS web API. In a future release they will
probably be represented by instances of field definition classes.)

The example above specifies a field called "text" which will be indexed as English
freetext (more on languages below) and will be stored in the database. Storing 
is not the same as indexing, and each will take up space in the database. Fields 
are not stored by default. 

If the data you are indexing is available from an external source (the Web, a 
RDBMS, a file system etc) you may want to save space by not storing the data in 
FSS, but fetching it from the external source as necessary. (Note, however, that 
FSS is an excellent, fast alternative to a RDBMS in many cases.)

Now we'll add a title field, which will be indexed and stored:

    $db->addField('title', array('freetext' => array('language' => 'en'), 
                                 'store' => true));

And an author field, which will be indexed as exacttext and stored:

    $db->addField('author', array('exacttext' => true, 'store' => true));

Note that exacttext does not take any sub-options.

The purpose of the language option in the freetext definition is so that words
extracted from the text can be "stemmed" appropriately. Stemming is used to 
normalise inflected forms of a word to improve search recall. For example, the
words "ski", "skis" and "skiing" all have the same topic, but without stemming
a search for "ski" would only find the first variant. With stemming, it will 
find all of them.

Since languages differ in their morphology, it is important to select the correct
language for stemming. See the API documentation for a list of supported langauges.
If no 'language' parameter is supplied, a field will not be stemmed.


Adding documents to the database
--------------------------------

Now the schema is set up, documents can be added to the database. Documents
are currently defined as arrays where keys are field names, pointing to field
values (again, this may change in a future release). Only fields which have
been explicitly defined in the schema should be used (in future, wildcards may
be used to provide default field behaviours).

The following code adds three documents (the first sentences of some random
books) to the database:

    $db->addDocument(array("title" => "Ham On Rye",
        "author" => "Charles Bukowski",
        "text" => "The first thing I remember is being under something."),
        "1-841-95163-3");

    $db->addDocument(array("title" => "Tales of the City",
        "author" => "Armistead Maupin",
        "text" => "Mary Ann Singleton was twenty-five years old ".
                  "when she saw San Francisco for the first time."),
        "0-552-99876-1");

    $db->addDocument(array("title" => "Matter",
        "author" => "Iain M. Banks",
        "text" => "A light breeze produced a dry rattling sound ".
                  "from some nearby bushes."),
        "978-1-84149-419-7");

    $db->commit();

Note the call to commit(). FSS batches database updates for efficiency, and
as a result documents may not be visible as soon as they are added. The commit
call ensures that any subsequent attempts to search for or otherwise access the
documents will succeed.

Also note that the ISBN codes have been supplied as explicit document IDs (the
second parameter to addDocument). If an ID is not supplied to addDocument, FSS
will assign a new unique ID.


Searching the database
----------------------

There are several search methods of different levels of complexity available.
The simplest is provided by the searchSimple database method. e.g.:

    $results = $db->searchSimple("first");
    echo $results["matches_estimated"] ." results found \n";
    
    foreach ($results["results"] as $r) {
        echo $r["rank"] .". ". $r['data']['title'][0] ."\n";
    }

Search results are returned as an array with various keys (yet another thing
that will be replaced with an object in a future release). The code above 
prints the estimated number of matching documents for the query, and the title
for each of the matches found. Note that only fields which are stored in the
database will be returned with the matching documents. Also note the [0] index
in the line which prints the title. This is because fields can have multiple
instances in a document, so each field is returned as an array (even in cases
such as this where documents have only one instance of each field.


Other documentation
-------------------

For more information, see docs/api.rst. There is also an example NewsML indexer
and web GUI search in the examples directory.



