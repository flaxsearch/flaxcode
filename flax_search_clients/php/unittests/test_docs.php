<?php

# Copyright (C) 2009 Lemur Consulting Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

#require_once('simpletest/autorun.php');
require_once('../flaxclient.php');
require_once('../flaxerrors.php');
require_once('_testrestclient.php');

error_reporting(E_ALL);

class DocsTestCase extends UnitTestCase {
    var $server;
    var $dbname;
    var $db;
    var $testcount = 0;

    function __construct($server) {
        $this->server = $server;
    }
    
    function setUp() {
        $this->dbname = 'tmp'. time();
        $this->db = $this->server->createDatabase($this->dbname);
        $this->db->addField('foo', array('type' => 'text', 
            'store' => true, 'freetext' => array()));
    }

    function tearDown() {
        $this->db->delete();
    }
    
    function testNoDoc() {        
        try {
            $fnames = $this->db->getDocument('doc001');
            $this->fail();
        }
        catch (FlaxDocumentError $e) {
            $this->pass();
        }
    }
    
    function testAddDoc() {
        # add a doc without ID
        $doc = array('foo' => 'bar');
        $docid = $this->db->addDocument($doc);

        # check it's been added ok
        $doc2 = $this->db->getDocument($docid);        
        $this->assertEqual($doc2['foo'], array('bar'));
    }
}

?>