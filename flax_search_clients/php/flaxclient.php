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

require_once('flaxerrors.php');

class _FlaxDatabase {
    private $restclient;
    private $dbname;
    private $is_deleted = false;
    
    function __construct($restclient, $dbname) {
        $this->restclient = $restclient;
        $this->dbname = $dbname;
    }
    
    function __toString() {
        $d = $self->is_deleted ? 'deleted' : '';
        return "_Flax_Database[{$this->dbname}{$d}]";
    }
    
    function delete() {
        $result = $this->restclient->do_delete($this->dbname);
        if ($result[0] != 200) {
            throw new FlaxDatabaseError($result[1]);
        }
    }
}

class FlaxSearchService {
    private $restclient;
    
    function __construct($baseurl, $restclient=null) {
        if ($restclient == null) {
            throw new FlaxInternalError('not implemented');
        } else {
            $this->restclient = $restclient;
        }
    }

    function getDatabase($name, $create=false) {
        # FIXME check database name for allowed characters
    
        $result = $this->restclient->do_get($name);
        if ($result[0] == 200) {
            return new _FlaxDatabase($this->restclient, $name);
        } else {
            if ($create) {
                $result2 = $this->restclient->do_post($name, true);
                if ($result2[0] == 201) {
                    return new _FlaxDatabase($this->restclient, $name);
                } else {
                    throw new FlaxDatabaseError('database could not be created ('. $result2[1] .')');
                }
            }
            throw new FlaxDatabaseError($result[1]);
        }
    }
}


?>