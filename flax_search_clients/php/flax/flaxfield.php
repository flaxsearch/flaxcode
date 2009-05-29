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
require_once('flaxjsonobject.php');

// Abstract field properties
abstract class FlaxField extends _FlaxJSONObject {
    public $store = false;
}

// Freetext field properties
class FlaxFreeTextField extends FlaxField {
    public $lang;

    function __construct($store=false, $lang=null) {
        $this->store = $store;
        $this->lang = $lang;
    }

    function toJSON() {
        $json = array('type' => 'text', 'store' => $this->store);
        if ($this->lang) {
            $json['freetext'] = array('language' => $this->lang);
        } else {
            $json['freetext'] = true;
        }

        return $json;
    }

    function __toString() {
        return "FlaxFreeTextField[{$this->store}, {$this->lang}]";
    }
}

// Exacttext field properties
class FlaxExactTextField extends FlaxField {
    function __construct($store=false) {
        $this->store = $store;
    }

    function toJSON() {
        return array('type' => 'text',
                     'store' => $this->store,
                     'exacttext' => true
                    );
    }

    function __toString() {
        return "FlaxExactTextField[{$this->store}]";
    }
}

// return a field
function flaxFieldFromJSON($json) {
    $store = $json['store'];

    if ($json['type'] == 'text') {
        if (array_key_exists('freetext', $json)) {
            return new FlaxFreeTextField($store, $json['freetext']['language']);
        } 
        else if (array_key_exists('exacttext', $json)) {
            return new FlaxExactTextField($store);
        }
        else {
            throw new FlaxFieldError('unsupported text field parameters');
        }
    } 
    else {
        throw new FlaxFieldError('unsupported field type');
    }
}

?>

