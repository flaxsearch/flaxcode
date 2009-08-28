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

error_reporting(E_ALL);

class FieldsTestCase extends UnitTestCase {
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
    
    function testNoFields() {
        $fnames = $this->db->getFieldNames();
        $this->assertIdentical($fnames, array());
        try {
            $this->db->getField('foo');
            $this->fail();
        }
        catch (FlaxFieldError $e) {
            $this->pass();
        }
    }
    
    function testAddDeleteFields() {
        # add a field
        $result = $this->db->addField('foo', new FlaxExactTextField(true));
        
        # flush changes
        # FIXME - make changes to DB structure commit automatically?
        # (can do at client or server level)
        $this->db->commit();
        
        # check it's been added ok
        $fnames = $this->db->getFieldNames();        
        $this->assertIdentical($fnames, array('foo'));

        $field = $this->db->getField('foo');
        $this->assertEqual($field->__toString(), 'FlaxExactTextField[1]');

        # delete the field
        $this->db->deleteField('foo');
        $this->db->commit();

        # check it's gone
        try {
            $this->db->getField('foo');
            $this->fail();
        }
        catch (FlaxFieldError $e) {
            $this->pass();
        }
    }
    
    function testOverwriteField() {
        # add a field
        $result = $this->db->addField('foo', new FlaxExactTextField(true));
        $this->db->commit();

        # check we can overwrite it
        $result = $this->db->replaceField('foo', new FlaxFreeTextField(true));
        $this->db->commit();

        # check it's been added ok
        $fnames = $this->db->getFieldNames();
        $this->assertIdentical($fnames, array('foo'));
        
        $field = $this->db->getField('foo');
        $this->assertIdentical($field->__toString(), 'FlaxFreeTextField[1, ]');
    }
}

?>
