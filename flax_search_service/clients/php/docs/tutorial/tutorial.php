<?php

// for details of this script, see tutorial.rst

require_once('../../flax/flaxclient.php');

// get a connection to the search service
$flax = new FlaxSearchService("http://localhost:8080/");

// create a new database
$db = $flax->createDatabase('my_database');

// set up a schema
$db->addField('text', array('freetext' => array('language' => 'en'), 
                            'store' => true));

$db->addField('title', array('freetext' => array('language' => 'en'), 
                             'store' => true));

$db->addField('author', array('exacttext' => true, 'store' => true));

// add some documents
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

// try a simple search
$results = $db->searchSimple("first");
echo $results["matches_estimated"] ." results found \n";
    
foreach ($results["results"] as $r) {
    echo (1 + $r["rank"]) .". ". $r['data']['title'][0] ."\n";
}

?>
