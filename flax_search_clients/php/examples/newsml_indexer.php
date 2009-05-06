<?php 

# Copyright (c) 2009 Lemur Consulting Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

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

foreach (array_slice($argv, 2) as $dir) {
    print "$dir\n";
    $dir_handle = opendir($dir);
    while ($file = readdir($dir_handle)) {
        if (preg_match('/\.xml$/', $file)) {
            $current_file = "${dir}/${file}";
            $fp = fopen($current_file, "r");
            if ($fp == false) {
                die();
            }
            $data = fread($fp, 1000000); 
            fclose($fp); 
    
            $xml_parser = xml_parser_create(); 
            xml_set_element_handler($xml_parser, "startTag", "endTag"); 
            xml_set_character_data_handler($xml_parser, "contents"); 
    
            if(!(xml_parse($xml_parser, $data, false))){ 
                print("Error on line " . xml_get_current_line_number($xml_parser)."\n"); 
            }         
            xml_parser_free($xml_parser);
        }
    }
    closedir($dir_handle);
}

$flaxdb->commit();

?>