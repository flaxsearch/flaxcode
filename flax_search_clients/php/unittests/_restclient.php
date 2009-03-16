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

    }

    function do_get($path, $params=null) {
        $bits = explode('/', $path);
        $dbname = $bits[0];
        if ($dbname == '') {
            return array(200, 'Flax Search Service (Test RestClient)');
        }
        
        if (array_key_exists($dbname, $this->dbs)) {
            $db = $this->dbs[$dbname];
            switch (count($bits)) {
                case 1:
                    return array(200, $db);
                    break;
                case 2:
                    if ($bits[1] == 'fields') {
                        return array(200, array_keys($db['_fields']));
                    }
                    break;
                case 3:
                    if (array_key_exists($bits[2], $db['_fields'])) {
                        return array(200, $db['_fields'][$bits[2]]);
                    }
                    break;
            }
        }

        return array(404, 'Path not found');
    }
    
    function do_post($path, $data) {
        $bits = explode('/', $path);
        $dbname = $bits[0];
        if ($dbname == '') {
            return array(405, 'Invalid method');
        }
        
        switch (count($bits)) {
            case 1:
                if ($data == true) {
                    $this->dbs[$dbname] = array(
                        'doccount' => 0,
                        'created_date' => new DateTime,
                        'last_modified_date' => new DateTime,
                        '_fields' => array()
                    );
                    return array(201, 'Database created');
                }
                break;
            case 3:
                if (array_key_exists($dbname, $this->dbs)) {
                    if ($bits[1] == 'fields') {
                        if ($data) {
                            $this->dbs[$dbname]['_fields'][$bits[2]] = $data;
                            return array(201, 'Field created');
                        }
                    }
                }
                break;
        }

        return array(404, 'Path not found');
    }

    function do_delete($path) {
        $bits = explode('/', $path);
        $dbname = $bits[0];
        if ($dbname == '') {
            return array(405, 'Invalid method');
        }
        
        if (count($bits) == 1) {
            unset($this->dbs[$dbname]);
            return array(200, 'Database deleted');
        } else if ($bits[1] == 'fields' && count($bits) == 3 && $bits[2] != '') {
            unset($this->dbs[$dbname]['_fields'][$bits[2]]);
            return array(200, 'Field deleted');
        } else {
            return array(404, 'Path not found');
        }
    }    

    function do_put($path, $data) {
        throw new FlaxError('not implemented');
    }    
}

?>