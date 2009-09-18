<?php
include_once "flax/flaxclient.php";

# open a connection to Flax Server
$conn = new FlaxSearchService('http://localhost:8080');

# create a database, overwriting any existing db with the same name
$db = $conn->createDatabase('books', true);

# add some field definitions
$db->addField('title', new FlaxFreeTextField(true, 'en'));
$db->addField('first', new FlaxFreeTextField(false, 'en'));
$db->addField('author', new FlaxExactTextField(true));

?>