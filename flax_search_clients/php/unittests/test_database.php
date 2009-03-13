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

class DatabaseTestCase extends UnitTestCase {
    var $server;
    var $dbname;
    var $testcount = 0;
    
    function setUp() {
        $this->server = new FlaxSearchService('', new FlaxTestRestClient);
        $this->dbname = 'temp-'. time();
    }

    function testNoDatabase() {
        try {
            $this->server->getDatabase($this->dbname);
            $this->fail();
        }
        catch (FlaxDatabaseError $e) {
        }
        $this->testcount++;
    }        

    function testCreateDeleteDatabase() {
        // create DB
        $db = $this->server->getDatabase($this->dbname, true);
        $this->assertNotNull($db);

        // check it exists
        $result = $this->server->getDatabase($this->dbname);
        $this->assertNotNull($result);

        // delete DB
        $db->delete();
        
        // check it has gone
        try {
            $this->server->getDatabase($this->dbname);
            $this->fail();
        }
        catch (FlaxDatabaseError $e) {
        }

        $this->testcount++;
    }
   

}

$test = &new DatabaseTestCase;
$ret = $test->run(new TextReporter()) ? 0 : 1;
print "passed {$test->testcount} tests\n";
exit($ret);

?>