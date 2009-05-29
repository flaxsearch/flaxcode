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

// class representing a single search result from Flax (a partial document
// with search metadata)
class FlaxSearchResult {
    public $docid;
    public $rank;
    public $weight;
    public $db;
    public $data;

    function __construct($json) {
        $this->docid = $json['docid'];
        $this->rank = $json['rank'];
        $this->weight = $json['weight'];
        $this->db = $json['db'];
        $this->data = $json['data'];
    }
}

// class representing a set of search results from Flax, plus metadata
class FlaxSearchResultSet {
    public $matches_estimated;
    public $estimate_is_exact;
    public $matches_lower_bound;
    public $matches_upper_bound;
    public $matches_human_readable_estimate;
    public $start_rank;
    public $end_rank;
    public $more_matches;
    public $results;

    function __construct($json) {
        $this->matches_estimated = $json['matches_estimated'];
        $this->estimate_is_exact = $json['estimate_is_exact'];
        $this->matches_lower_bound = $json['matches_lower_bound'];
        $this->matches_upper_bound = $json['matches_upper_bound'];
        $this->matches_human_readable_estimate = $json['matches_human_readable_estimate'];
        $this->start_rank = $json['start_rank'];
        $this->end_rank = $json['end_rank'];
        $this->more_matches = $json['more_matches'];
    
        $len = count($json['results']);
        if ($len) {
            $this->results = array_fill(0, $len, null);
            for ($i = 0; $i < $len; $i++) {
                $this->results[$i] = new FlaxSearchResult($json['results'][$i]);
            }
        }
        else {
            $this->results = array();
        }
    }
}

?>

