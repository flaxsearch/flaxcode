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

class SearchTestCase extends UnitTestCase {
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
    }

    function tearDown() {
        $this->db->delete();
    }
    
    function testExact() {
        # test exact indexing and search

        $this->db->addField('f1', array('exacttext' => True));
        $this->db->addField('f2', array('exacttext' => True));

        $this->db->addDocument(array('f1' => 'Billy Bragg', 'f2' => 'A New England'), 'doc1');
        $this->db->addDocument(array('f1' => 'Billy Bragg', 'f2' => 'Between The Wars'), 'doc2');
        $this->db->commit();

        # check search results
        $results = $this->db->searchJSON(array('query_fields' => 
            array('f2' => 'A New England')));
        
        $this->assertEqual($results['matches_estimated'], 1);
        $this->assertEqual($results['results'][0]['docid'], 'doc1');

        $results = $this->db->searchJSON(array('query_fields' => 
            array('f2' => 'Between The Wars')));
        $this->assertEqual($results['matches_estimated'], 1);
        $this->assertEqual($results['results'][0]['docid'], 'doc2');

        $results = $this->db->searchJSON(array('query_fields' => 
            array('f1' => 'Billy Bragg')));
        $this->assertEqual($results['matches_estimated'], 2);

        $results = $this->db->searchJSON(array('query_fields' => 
            array('f1' => 'Billy Bragg', 'f2' => 'A New England')));
        $this->assertEqual($results['matches_estimated'], 1);
    }
    
    function testFreetext() {
        $this->db->addField('f1', array('exacttext' => True));
        $this->db->addField('f2', array('freetext' => True));
    
        $this->db->addDocument(array('f1' => 'Billy Bragg', 'f2' => 'A New England'), 'doc1');
        $this->db->addDocument(array('f1' => 'Billy Bragg', 'f2' => 'between the wars'), 'doc2');
        $this->db->commit();
    
        # check search results (field search)
        $results = $this->db->searchJSON(array('query_fields' => 
            array('f2' => 'A New England')));      
        $this->assertEqual($results['matches_estimated'], 1);
        $this->assertEqual($results['results'][0]['docid'], 'doc1');

        # check search results (freetext search)
        $results = $this->db->searchSimple('A New england');
        $this->assertEqual($results['matches_estimated'], 1);
        $this->assertEqual($results['results'][0]['docid'], 'doc1');

        # check search results (freetext search)
        $results = $this->db->searchSimple('Between The Wars');
        $this->assertEqual($results['matches_estimated'], 1);
        $this->assertEqual($results['results'][0]['docid'], 'doc2');
    }

    function testFreetextStemmed() {
        $this->db->addField('f1', array('freetext' => array('language' => 'en')));
        $this->db->addDocument(array('f1' => 'A New England'), 'doc1');
        $this->db->addDocument(array('f1' => 'between the wars'), 'doc2');
        $this->db->commit();

        $results = $this->db->searchSimple('warring');
        $this->assertEqual($results['matches_estimated'], 1);

        $results = $this->db->searchSimple('warring between');
        $this->assertEqual($results['matches_estimated'], 1);

        $results = $this->db->searchSimple('war OR england');
        $this->assertEqual($results['matches_estimated'], 2);

    }
    
}

?>