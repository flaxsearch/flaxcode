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

require_once('flaxerrors.php');
require_once('flaxfield.php');
require_once('_restclient_curl.php');

class FlaxSearchService {
    private $restclient;
    
    function __construct($url) {
    	if (substr($url, strlen($url) - 1) != '/') {
	    $url = $url . '/';
	}
        $this->restclient = new FlaxRestClient($url, 1);
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
    
    function getDocCount() {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }
        
        $result = $this->restclient->do_get('dbs/'._uencode($this->dbname));
        if ($result[0] != 200) {
            throw new FlaxFieldError($result[1]);
        }
        
        return $result[1]['doccount'];    
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
        
        return flaxFieldFromJSON($result[1]);
    }

    function addField($fieldname, $fielddesc) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_post(
            'dbs/'._uencode($this->dbname).'/schema/fields/'._uencode($fieldname), 
            $fielddesc->toJSON());

        if ($result[0] != 200) {
            throw new FlaxFieldError($result[1]);
        }
    }

    function replaceField($fieldname, $fielddesc) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_put(
            'dbs/'._uencode($this->dbname).'/schema/fields/'._uencode($fieldname), 
            $fielddesc->toJSON());

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

    function commit() {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $result = $this->restclient->do_post(
            'dbs/'._uencode($this->dbname).'/flush', 'true');
            
        if ($result[0] != 200) {
            throw new FlaxFieldError($result[1]);
        }
    }
    
    function searchSimple($query, $start_rank=0, $end_rank=10) {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $url = 'dbs/'._uencode($this->dbname).'/search/simple?query='._uencode($query).
               '&start_rank='.$start_rank.'&end_rank='.$end_rank;
        $result = $this->restclient->do_get($url);
    
        if ($result[0] != 200) {
            throw new FlaxDocumentError($result[1]);
        }
        
        return $result[1];
    }

    function searchStructured($query_all, $query_any, $query_none, $query_phrase,
                              $filters=array(), $start_rank=0, $end_rank=10) 
    {
        if ($this->deleted) {
            throw new FlaxDatabaseError('database has been deleted');
        }

        $url = 'dbs/'._uencode($this->dbname).'/search/structured?start_rank='.$start_rank.
               '&end_rank='.$end_rank.'&query_all='._uencode($query_all).
               '&query_any='._uencode($query_any).'&query_none='._uencode($query_none).
               '&query_phrase='._uencode($query_phrase);
        
        foreach ($filters as $filter) {
            $url .= '&filter='._uencode($filter[0].':'.$filter[1]);
        }
        
        $result = $this->restclient->do_get($url);
    
        if ($result[0] != 200) {
            throw new FlaxDocumentError($result[1]);
        }
        
        return $result[1];
    }

    function searchSimilar($id, $start_rank = 0, $end_rank = 10, $pcutoff = null) 
    {
	if($this->deleted) {
		throw new FlaxDatabaseError('database has been deleted');
	}

	$url = 	'dbs/'._uencode($this->dbname).'/search/similar?start_rank='.intval($start_rank).
		'&end_rank='.intval($end_rank).'&id=' . _uencode($id);
	
	if(intval($pcutoff)) 
	{
		$url .= '&pcutoff='.$pcutoff;
	}

	$result = $this->restclient->do_get($url);
        
	if ($result[0] != 200) {
            throw new FlaxDocumentError($result[1]);
        }

	return $result[1];
    }

}

function _uencode($s) {
    return str_replace('-', '%2D', urlencode("{$s}"));
}

?>
