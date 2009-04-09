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
 * FIXME
 */

require_once('flaxerrors.php');

class FlaxRestClient {
    function __construct($baseurl=null) {
        $this->baseurl = $baseurl;
    }

    function do_get($path, $params=null) {
        $url = $this->baseurl.$path;
        if (is_array($params)) {
            $url .= '?'. http_build_query($params);
        }
        else if ($params != null) {
            throw new FlaxDataError('GET params must be in an array');
        }
        return $this->_do_http_request($url, 'GET');
    }
        
    function do_post($path, $data='') {
        return $this->_do_http_request($this->baseurl.$path, 'POST', $data);
    }

    function do_put($path, $data='') {
        return $this->_do_http_request($this->baseurl.$path, 'PUT', $data);
    }

    function do_delete($path) {
        return $this->_do_http_request($this->baseurl.$path, 'DELETE');
    }
    
    function _do_http_request($url, $method='GET', $content=null) {
        $http = array('method'  => $method, 'timeout' => 30);
        if ($content != null) {
            $json_content = json_encode($content);
            $content_length = strlen($json_content);
            $http['content'] = $json_content;
            $http['header'] = "Content-type: text/json\r\n" .
                "Content-length: {$content_length}\r\n";
        }
        
        $options = array('http' => $http);
        $context = stream_context_create($options);
        $retbody = @file_get_contents($url, false, $context);

        if (!isset($http_response_header)) {
            throw new FlaxInternalError("error communicating with server ({$url})");
        }
        
        // Get the *last* HTTP status code
        $nLines = count($http_response_header);
        for ($i = $nLines-1; $i >= 0; $i--)
        {
            $line = $http_response_header[$i];
            if (strncasecmp("HTTP", $line, 4) == 0)
            {
                $response = explode(' ', $line);
                $http_code = $response[1];
                $http_message = $line;
                break;
            }
        }
     
        if (substr($http_code, 0, 1) == '2') {
            return array($http_code, json_decode($retbody, true));
        } else {
            return array($http_code, $http_message);
        }
    }
}

