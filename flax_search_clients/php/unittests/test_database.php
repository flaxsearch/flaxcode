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

class TestOfLogging extends UnitTestCase {
    var $server;
    var $dbname;
    
    function setUp() {
        $this->server = new FlaxSearchService('', new FlaxTestRestClient);
        $this->dbname = 'temp-'. time();
    }

    function testNoDatabase() {
        try {
            $result = $this->server->getDatabase($this->dbname);
            $this->assertTrue(false);
        }
        catch (FlaxDatabaseError $e) {
        }
    }        

    function testCreateDatabase() {
        $result = $this->server->getDatabase($this->dbname, true);
        $this->assertNotNull($result);
    }        

}


?>