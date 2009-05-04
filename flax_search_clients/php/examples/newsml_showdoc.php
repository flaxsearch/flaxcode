<?php 

$xsl = new DomDocument;
$xsl->load('newsml.xsl');

$xp = new XsltProcessor();
$xp->importStylesheet($xsl);

$path = $_GET['path'];
$xml_doc = new DomDocument;
$xml_doc->load($path);

if ($html = $xp->transformToXML($xml_doc)) {
    echo $html;
} else {
    trigger_error('XSL transformation failed.', E_USER_ERROR);
}
?>

