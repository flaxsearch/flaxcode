<?php
include_once "flax/flaxclient.php";

# open a connection to Flax Server
$conn = new FlaxSearchService('http://localhost:8080');

# get a reference to the database
$db = $conn->getDatabase('books');

# fetch and print the document
print_r($db->getDocument($argv[1]));

?>