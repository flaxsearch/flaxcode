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

require_once('simpletest/autorun.php');
require_once('../flaxclient.php');
require_once('../flaxerrors.php');
require_once('_restclient.php');

error_reporting(E_ALL);

class FieldsTestCase extends UnitTestCase {
    var $server;
    var $dbname;
    var $db;
    var $testcount = 0;
    
    function setUp() {
        $this->server = new FlaxSearchService('', new FlaxTestRestClient);
        $this->dbname = 'temp-'. time();
        $this->db = $this->server->getDatabase($this->dbname, true);
    }

    function tearDown() {
        $this->db->delete();
    }
    
    function testNoFields() {
        $fnames = $this->db->getFieldNames();
        $this->assertIdentical($fnames, array());
        try {
            $this->db->getField('foo');
            $this->fail();
        }
        catch (FlaxFieldError $e) {
        }
        
        $this->testcount++;
    }
    
    function testAddDeleteFields() {
        # add a field
        $fielddesc = array('store' => true, 'exacttext' => true);
        $result = $this->db->setField('foo', $fielddesc);
    
        # check it's been added ok
        $field = $this->db->getField('foo');
        $this->assertIdentical($field, $fielddesc);
        
        # delete the field
        $this->db->deleteField('foo');

        # check it's gone
        try {
            $this->db->getField('foo');
            $this->fail();
        }
        catch (FlaxFieldError $e) {
        }

        $this->testcount++;
    }
}

$test = &new FieldsTestCase;
$ret = $test->run(new TextReporter()) ? 0 : 1;
print "passed {$test->testcount} tests\n";
exit($ret);

?>