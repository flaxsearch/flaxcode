<?php
include_once "flax/flaxclient.php";

# open a connection to Flax Server
$conn = new FlaxSearchService('http://localhost:8080');

# get a reference to the database
$db = $conn->getDatabase('books');

# documents are arrays with fieldnames as keys and strings (or lists of
# strings) as values
$doc = array();

foreach (file($argv[1]) as $line)
{
    $matches = array();
    if (preg_match('/(\w+):\s+(.+)/', $line, $matches))
    {
        $name = $matches[1];
        $value = $matches[2];
        if ($name == 'isbn')
        {
            # add the document, using ISBN as the ID
            $db->addDocument($doc, $value);
            $doc = array();
        }
        else
        {
            # add the field to the document
            $doc[$name] = $value;
        }
    }
}

# commit the documents to the database
$db->flush();

?>