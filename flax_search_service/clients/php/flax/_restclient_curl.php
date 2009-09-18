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
 
/**
 * FIXME
 */

require_once('flaxerrors.php');

class FlaxRestClient {
    function __construct($baseurl=null, $version=1) {
        $this->baseurl = $baseurl . "v$version/";
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
			      "Content-length: {$content_length}",
			      "Connection: Keep-Alive",
			      "Expect:"));                        // 100-Continue causes problems with server
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
?>