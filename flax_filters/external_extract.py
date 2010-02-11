# Copyright (C) 2009, 2010 Lemur Consulting Ltd
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


import subprocess

def get_stdout(command_line):
    return subprocess.Popen(command_line,
                            stdout=subprocess.PIPE,
                            stderr=None).stdout

def external_filter(command_line):
    """command_line should contain a list of strings to invoke an
    external program in such way then it returns text on standard
    output.

    """
    for line in get_stdout(command_line):
        yield 'textcontent', line
        

# Filters using command line tools follow

def pdftotext_filter(filename):
    """
    A filter that uses pdftotext to generate text.
    For Windows: 
        Obtain pdftotext from http://www.foolabs.com/xpdf/download.html
        It must be on your PATH
    """
    
    return external_filter(['pdftotext', filename, '-'])

def antiword_filter(filename):
    """
    A filter that uses antiword to generate text.
    For Windows: 
        Obtain antiword from http://www.informatik.uni-frankfurt.de/~markus/antiword/
        It must be on your PATH and may object if a HOME directory has not been set.
    """
    return external_filter(['antiword', filename])
