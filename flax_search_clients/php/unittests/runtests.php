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

require_once('simpletest/unit_tester.php');
require_once('simpletest/reporter.php');

require_once('../flaxclient.php');
require_once('test_database.php');
require_once('test_fields.php');
require_once('test_docs.php');
require_once('test_search.php');

$server = null;
$server_url = null;
$tests = array();

foreach ($argv as $a) {
    if (substr($a, 0, 7) == 'http://') {
        $server_url = $a;
    } else if ($a != $argv[0]) {
        $tests[$a] = true;
    }    
}

if ($server_url) {
    $server = new FlaxSearchService($server_url);
} else {
#    $server = new FlaxSearchService(new FlaxTestRestClient());
    die("URL for search service required\n");
}

$test = new TestSuite('All tests');
if (!$tests || array_key_exists('dbs', $tests))
    $test->addTestCase(new DatabaseTestCase($server));

if (!$tests || array_key_exists('fields', $tests))
    $test->addTestCase(new FieldsTestCase($server));

if (!$tests || array_key_exists('docs', $tests))
    $test->addTestCase(new DocsTestCase($server));

if (!$tests || array_key_exists('search', $tests))
    $test->addTestCase(new SearchTestCase($server));

exit($test->run(new TextReporter()) ? 0 : 1);

?>
