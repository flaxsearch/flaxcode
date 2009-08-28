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
        $http = array('method'  => $method,
		      'timeout' => 30,
		      'max_redirects' => 0, // stops it redirecting
		      'ignore_errors' => true // returns the content on error
		     );
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
            return array($http_code, $http_message . ' (' . $retbody . ')');
        }
    }
}
