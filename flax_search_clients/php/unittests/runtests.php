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

require_once('test_database.php');
require_once('test_fields.php');

$test = new TestSuite('All tests');
$test->addTestCase(new DatabaseTestCase(count($argc) > 1 ? $argv[1] : null));
$test->addTestCase(new FieldsTestCase(count($argc) > 1 ? $argv[1] : null));

exit($test->run(new TextReporter()) ? 0 : 1);

?>
