<?php 
require_once('../flax/flaxclient.php');

$query = isset($_GET['query']) ? $_GET['query'] : '';
if ($query) {
    $flax = new FlaxSearchService("http://localhost:8080/");
    $db = $flax->getDatabase("newsml");
    $results = $db->searchSimple($query);
}

?>

<html>
<head>
<title>Flax PHP Search Example</title>
</head>
<body>

<form method="GET">
    <input name="query" value="<?=$query?>"/>
    <input type="submit" value="Search"/>
</form>

<?
if ($query) {
    if ($results['matches_estimated']) {
?>
        <p>
        <?=$results['start_rank'] + 1 ?> to <?=$results['end_rank'] ?> of 
        <?=$results['estimate_is_exact'] ? '' : 'about ' ?>
        <?=$results['matches_estimated'] ?> matching documents out of
        <?=$db->getDocCount() ?>
        </p>
<?
        foreach ($results['results'] as $r) {
?>        
            <?=$r['rank'] + 1 ?>.
            <a href="newsml_showdoc.php?path=<?=$r['data']['_PATH'][0]?>" 
               target="doc"><?=$r['data']['HEADLINE'][0] ?></a>
            <br/>
<?
        }
    }
    else {
        print "<p>No matching documents found</p>\n";
    }
}
?>

</body>
</html>
