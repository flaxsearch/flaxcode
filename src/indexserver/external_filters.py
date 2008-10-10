from __future__ import with_statement
# Copyright (C) 2007 Lemur Consulting Ltd
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
"""Filters that extract text by invoking an external program."""

import itertools
import subprocess

import htmltotext_filter

def get_sdtout(command_line):
    return subprocess.Popen(command_line,
                            stdout=subprocess.PIPE).stdout

def external_filter(command_line):
    """command_line should contain a list of strings to invoke an
    external program in such way then it returns text on standard
    output.

    """
    for line in get_sdtout(command_line):
        yield 'content', line

def pdftotext_filter(filename):
    """A filter that uses pdftotext to generate text."""
    return external_filter(['pdftotext', filename, '-'])

def antiword_filter(filename):
    """A filter that uses antiword to generate text."""
    return external_filter(['antiword', filename])

def xls2csv_filter(filename):
    """A filter that uses xls2csv to generate text."""
    return external_filter(['xls2csv', filename])

def ppthtml_filter(filename):
    """A filter that uses ppthtml to extract html from a powerpoint
    file, and then uses the htmltotext filter to extract text from
    that.

    """
    ppthtmlout = get_sdtout(["ppthtml", filename])
    return htmltotext_filter.html_filter_from_stream(ppthtmlout.read())
                                         
