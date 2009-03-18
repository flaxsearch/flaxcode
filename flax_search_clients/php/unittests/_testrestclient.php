<?php

/* Copyright (C) 2009 Lemur Consulting Ltd
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 * 
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License along
 * with this program; if not, write to the Free Software Foundation, Inc.,
 * 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
 */
 
/**
 * Class faking a RestClient for the purposes of testing. This doesn't actually
 * access any remote resource, but acts like it does.
 *
 */

require_once('../flaxerrors.php');

class FlaxTestRestClient {
    function __construct($baseurl=null) {
        $this->baseurl = $baseurl;
        $this->dbs = array();
        
        $this->patterns = array(
            # more complex ones first!
            array('/^dbs\/(.+)\/schema\/fields\/(.+)$/', 'f_field'),
            array('/^dbs\/(.+)\/schema\/fields$/',       'f_fields'),
            array('/^dbs\/(.+)$/',                       'f_db'),
            array('/^dbs$/',                             'f_dbs'),
            array('/^$/',                                'f_root')
        );
    }

    function match_path($path) {
        foreach ($this->patterns as $p) {
            $groups = array();
            if (preg_match($p[0], $path, $groups)) {
                return array($p[1], $groups);
            }
        }
        return null;
    }

    function do_get($path, $params=null) {
        $groups = null;
        $m = $this->match_path($path);
        if ($m) {
            return $this->$m[0]('GET', $m[1], $params, null);
        }
        return array(404, 'Path not found');
    }
        
    function do_post($path, $data='') {
        $groups = null;
        $m = $this->match_path($path);
        if ($m) {
            return $this->$m[0]('POST', $m[1], null, $data);
        }
        return array(404, 'Path not found');
    }

    function do_put($path, $data='') {
        $groups = null;
        $m = $this->match_path($path);
        if ($m) {
            return $this->$m[0]('PUT', $m[1], null, $data);
        }
        return array(404, 'Path not found');
    }

    function do_delete($path) {
        $groups = null;
        $m = $this->match_path($path);
        if ($m) {
            return $this->$m[0]('DELETE', $m[1], null, null);
        }
        return array(404, 'Path not found');
    }
    
    function f_root($method, $pathparams, $queryparams, $bodydata) {
        if ($method == 'GET') {
            return array(200, 'Flax Search Service (Test RestClient)');
        }
        return array(404, 'Path not found');
    }

    function f_dbs($method, $pathparams, $queryparams, $bodydata) {
        if ($method == 'GET') {
            return array_keys($this->dbs);
        }
        return array(404, 'Path not found');
    }

    function f_db($method, $pathparams, $queryparams, $bodydata) {
        $dbname = $pathparams[1];
        if ($method == 'GET') {
            if (array_key_exists($dbname, $this->dbs)) {
                return array(200, $this->dbs[$dbname]);
            }
        }
        else if ($method == 'POST') {
            $this->dbs[$dbname] = array(
                'doccount' => 0,
                'created_date' => new DateTime,
                'last_modified_date' => new DateTime,
                '_fields' => array()
            );
            return array(201, 'Database created');
        }
        else if ($method == 'DELETE') {        
            unset($this->dbs[$dbname]);
            return array(200, 'Database deleted');
        }
        
        return array(404, 'Path not found');
    }

    function f_fields($method, $pathparams, $queryparams, $bodydata) {
        $dbname = $pathparams[1];
        if ($method == 'GET') {
            if (array_key_exists($dbname, $this->dbs)) {
                return array(200, array_keys($this->dbs[$dbname]['_fields']));
            }
        }
        return array(404, 'Path not found');
    }

    function f_field($method, $pathparams, $queryparams, $bodydata) {
        $dbname = $pathparams[1];
        $fieldname = $pathparams[2];
        if (array_key_exists($dbname, $this->dbs)) {
            $db = $this->dbs[$dbname];
            if ($method == 'GET') {
                if (array_key_exists($fieldname, $db['_fields'])) {
                    return array(200, $db['_fields'][$fieldname]);
                }
            }
            else if ($method == 'POST') {
                if (array_key_exists($fieldname, $db['_fields'])) {
                    return array(409, 'Field exists');
                }
                $this->dbs[$dbname]['_fields'][$fieldname] = $bodydata;
                return array(201, 'Field created');
            }            
            else if ($method == 'PUT') {
                $this->dbs[$dbname]['_fields'][$fieldname] = $bodydata;
                return array(201, 'Field created');
            }            
            else if ($method == 'DELETE') {
                if (array_key_exists($fieldname, $db['_fields'])) {
                    unset($this->dbs[$dbname]['_fields'][$fieldname]);
                    return array(200, 'Field deleted');
                }
            }
        }
        return array(404, 'Path not found');    
    }
}

?>
