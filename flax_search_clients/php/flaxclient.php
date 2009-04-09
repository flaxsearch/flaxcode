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
require_once('_restclient.php');

class FlaxSearchService {
    private $restclient;
    
    function __construct($restclient=null) {
        $this->restclient = $restclient;
    }

    function getDatabase($name) {
        $result = $this->restclient->do_get('dbs/'._uencode($name));
        if ($result[0] == 200) {
            return new _FlaxDatabase($this->restclient, $name);
        } 
        else {
            throw new FlaxDatabaseError($result[1]);
        }
    }
    
    function createDatabase($name, $overwrite=false, $reopen=false) {
        $params = array('overwrite' => (int) $overwrite,
                        'reopen'    => (int) $reopen);

        $result = $this->restclient->do_post('dbs/'._uencode($name), $params);
        if ($result[0] == 200) {
            return new _FlaxDatabase($this->restclient, $name);
        } else {
            throw new FlaxDatabaseError('database could not be created ('. $result[1] .')');
        }
    }
}

class _FlaxDatabase {
    private $restclient;
    private $dbname;
    private $deleted = false;
    
    function __construct($restclient, $dbname) {
        $this->restclient = $restclient;
        $this->dbname = $dbname;
    }
    
    function __toString() {
        $d = $self->deleted ? 'deleted' : '';
        return "_Flax_Database[{$this->dbname}{$d}]";
    }
    
    function delete() {
        $result = $this->restclient->do_delete('dbs/'._uencode($this->dbname));
        if ($result[0] != 200) {
            throw new FlaxDatabaseError($result[1]);
        }
        $this->deleted = true;
    }
    
    function getFieldNames() {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }
        
        $result = $this->restclient->do_get('dbs/'._uencode($this->dbname).'/schema/fields');
        if ($result[0] != 200) {
            throw new FlaxFieldError($result[1]);
        }
        
        return $result[1];
    }
    
    function getField($fieldname) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_get(
            'dbs/'._uencode($this->dbname).'/schema/fields/'._uencode($fieldname));
            
        if ($result[0] != 200) {
            throw new FlaxFieldError($result[1]);
        }
        
        return $result[1];
    }

    function addField($fieldname, $fielddesc) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_post(
            'dbs/'._uencode($this->dbname).'/schema/fields/'._uencode($fieldname), $fielddesc);

        if ($result[0] != 200) {
            throw new FlaxFieldError($result[1]);
        }
    }

    function replaceField($fieldname, $fielddesc) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_put(
            'dbs/'._uencode($this->dbname).'/schema/fields/'._uencode($fieldname), $fielddesc);

        if ($result[0] != 200) {
            throw new FlaxFieldError($result[1]);
        }
    }

    function deleteField($fieldname) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_delete(
            'dbs/'._uencode($this->dbname).'/schema/fields/'._uencode($fieldname));
            
        if ($result[0] != 200) {
            throw new FlaxFieldError($result[1]);
        }
    }

    function getDocument($docid) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_get(
            'dbs/'._uencode($this->dbname).'/docs/'._uencode($docid));
    
        if ($result[0] != 200) {
            throw new FlaxDocumentError($result[1]);
        }
        
        return $result[1];
    }
    
    function addDocument($docdata, $docid=null) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        if ($docid) {
            $result = $this->restclient->do_post(
                'dbs/'._uencode($this->dbname).'/docs/'._uencode($docid), $docdata);
        } else {
            $result = $this->restclient->do_post(
                'dbs/'._uencode($this->dbname).'/docs', $docdata);
        }
        
        # FIXME - Location header for docid return
        # (except it breaks the PHP HTTP lib)  =(
        if ($result[0] != 200) {
            throw new FlaxDocumentError($result[1]);
        }

        return "{$result[1]}";
    }

    function replaceDocument($docid, $docdata) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_put(
            'dbs/'._uencode($this->dbname).'/docs/'._uencode($docid), $docdata);

        if ($result[0] != 200) {
            throw new FlaxDocumentError($result[1]);
        }
        
        return $result[1];
    }
    
    function deleteDocument($docid) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_delete(
            'dbs/'._uencode($this->dbname).'/docs/'._uencode($docid));

        if ($result[0] != 200) {
            throw new FlaxDocumentError($result[1]);
        }
    }
}

function _uencode($s) {
    return str_replace('-', '%2D', urlencode("{$s}"));
}

?>