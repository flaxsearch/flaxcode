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
"""Simple filter for plain text documents.

"""
from __future__ import with_statement
__docformat__ = "restructuredtext en"

import itertools

def text_filter(filename):

    def start_fields():
        yield ("filename", filename)
        raise StopIteration

    def get_paragraphs():
        with open(filename) as f:
            for k, para in itertools.groupby(f, lambda x: "\n" == x):
                if not k: #get rid of the blank line groups
                    yield "content", ''.join(para)
                

    return itertools.chain(start_fields(), get_paragraphs())
