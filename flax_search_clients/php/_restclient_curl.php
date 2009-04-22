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
        $this->ch = null;
    }

    function __destruct() {
        if ($this->ch != null)
	    curl_close($this->ch);
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
    
    function _read_callback($ch, $data) {
        $data = $this->putdata;
	return count($this->putdata);
    }

    /* Perform an HTTP request.
     *
     * Returns an array containing the http response code followed by the
     * response body.  If the response code is a success code, the response
     * body is assumed to have been JSON encoded, and the returned value is the
     * result of decoding it.
     */
    function _do_http_request($url, $method='GET', $content=null) {
        if ($this->ch != null) {
	    curl_close($this->ch);
	}
    	$this->ch = curl_init();

	curl_setopt($this->ch, CURLOPT_URL, $url);
	curl_setopt($this->ch, CURLOPT_HEADER, 1);
	curl_setopt($this->ch, CURLOPT_FOLLOWLOCATION, 0);
	curl_setopt($this->ch, CURLOPT_RETURNTRANSFER, 1);
	curl_setopt($this->ch, CURLOPT_CONNECTTIMEOUT, 15);
	curl_setopt($this->ch, CURLOPT_USERAGENT, "Flax-PHP-curl client");

        if ($content != null) {
            $json_content = json_encode($content);
            $content_length = strlen($json_content);
	    curl_setopt($this->ch, CURLOPT_POSTFIELDS, $json_content);
	    curl_setopt($this->ch, CURLOPT_HTTPHEADER,
			array("Content-type: text/json",
			      "Content-length: {$content_length}"));
	}

	switch ($method) {
	    case "GET":
		curl_setopt($this->ch, CURLOPT_HTTPGET, true);
		break;
	    case "POST":
		curl_setopt($this->ch, CURLOPT_POST, true);
		break;
	    case "PUT":
		curl_setopt($this->ch, CURLOPT_CUSTOMREQUEST, $method);
		break;
	    case "DELETE":
		curl_setopt($this->ch, CURLOPT_CUSTOMREQUEST, $method);
		break;
	    default:
	        throw new FlaxInternalError("Unknown HTTP method: ($method)");
	}

	$response = curl_exec($this->ch);
	$error = curl_error($this->ch);
	if ($error != "") {
            throw new FlaxInternalError("error communicating with server ($method: {$url} - {$error})");
	}
	if ($response == false) {
            throw new FlaxInternalError("error communicating with server ($method: {$url})");
	}

	$header_size = curl_getinfo($this->ch,CURLINFO_HEADER_SIZE);
	$headers = explode('\n', substr($response, 0, $header_size));
	$location = null;
        $nLines = count($headers);
        for ($i = $nLines - 1; $i >= 0; $i--)
        {
	    $line = $headers[$i];
            if (strncasecmp("Location:", $line, 9) == 0)
            {
	        $location = substr($line, 10);
	    }
	}

        $retbody = substr($response, $header_size);
	$http_code = curl_getinfo($this->ch, CURLINFO_HTTP_CODE);

        if (substr($http_code, 0, 1) == '2') {
            return array($http_code, json_decode($retbody, true), $location);
        } else {
            return array($http_code, $retbody, $location);
        }
    }
}
