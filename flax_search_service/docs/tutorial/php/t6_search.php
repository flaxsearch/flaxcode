<?php
include_once "flax/flaxclient.php";

# open a connection to Flax Server
$conn = new FlaxSearchService('http://localhost:8080');

# get a reference to the database
$db = $conn->getDatabase('books');

# do the search and get the results
$results = $db->searchSimple($argv[1]);

if ($results->results)
{
    # print a summary of the results
    printf("%d to %d of %s results:\n", $results->start_rank + 1, 
        $results->end_rank,
        $results->matches_human_readable_estimate);
    
    # print the rank and title of each result
    foreach ($results->results as $hit)
    {
        printf("(%s) %s\n", $hit->rank + 1, $hit->data['title'][0]);
    }
}
else
{
    print "no results\n";
}
    
?>