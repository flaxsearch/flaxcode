<?php 

require_once('../flaxclient.php');

$fieldname = $docdata = $doc = null;
$current_file = null;

function contents($parser, $data){
    global $fieldname, $docdata;
    
    if ($fieldname) {
        $docdata .= $data;
    }
} 

function startTag($parser, $name, $attrs){ 
    global $fieldname, $docdata, $doc, $current_file;

    if ($name == 'NEWSITEM') {
        $doc = array('_PATH' => $current_file);
    } 
    else if ($name == 'HEADLINE' || $name == 'BYLINE' || 
               $name == 'DATELINE' || $name == 'TEXT') {
        $docdata = '';
        $fieldname = $name;
    }
} 

function endTag($parser, $name){ 
    global $fieldname, $docdata, $doc;

    if ($name == 'NEWSITEM') {
        add_document();
    } 
    else if ($name == 'HEADLINE' || $name == 'BYLINE' || 
               $name == 'DATELINE' || $name == 'TEXT') {
        $doc[$fieldname] = $docdata;        
        $fieldname = null;
    }
} 

function add_document() {
    global $doc, $flaxdb;
    $flaxdb->addDocument($doc);
}

$flax = new FlaxSearchService($argv[1]);
$flaxdb = $flax->createDatabase('newsml');

$flaxdb->addField('HEADLINE', array('store' => true, 
    'freetext' => array('language' => 'en', 'term_frequency_multiplier' => 3)));

$flaxdb->addField('BYLINE', array('store' => true, 'exacttext' => true));
$flaxdb->addField('DATELINE', array('store' => true, 'exacttext' => true));
$flaxdb->addField('TEXT', array('store' => false, 'freetext' => array('language' => 'en')));
$flaxdb->addField('_PATH', array('store' => true));
$flaxdb->commit();

$dir_handle = opendir($argv[2]);
while ($file = readdir($dir_handle)) {
    if (preg_match('/\.xml$/', $file)) {
        $current_file = "${argv[2]}/${file}";
        print "$current_file\n";
        $fp = fopen($current_file, "r"); 
        $data = fread($fp, 1000000); 

        $xml_parser = xml_parser_create(); 
        xml_set_element_handler($xml_parser, "startTag", "endTag"); 
        xml_set_character_data_handler($xml_parser, "contents"); 

        if(!(xml_parse($xml_parser, $data, false))){ 
            print("Error on line " . xml_get_current_line_number($xml_parser)."\n"); 
        }         
        xml_parser_free($xml_parser);
    }
}

fclose($fp); 
$flaxdb->commit();

?>