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
"""Filter for XML documents (for the service branch)

"""

from __future__ import with_statement
import xml.sax

_doc_tag = 'document'

class Handler(xml.sax.ContentHandler):
    def __init__(self):
        self.fields = []
        
    def startElement(self, tag, attrs):
        if tag == _doc_tag:
            self.fields.append(('_docid', attrs['id']))
        self.data = []
    
    def endElement(self, tag):
        if tag != _doc_tag:
            self.fields.append ((tag, ''.join(self.data)))
    
    def characters(self, data):
        self.data.append(data)

def xml_filter(filename):
    p = xml.sax.make_parser()
    h = Handler()
    p.setContentHandler(h)
    with open(filename) as f:
        while True:
            data = f.read(4096)
            if not data: break
            p.feed(data)
        
    p.close()
    return h.fields
        
if __name__ == '__main__':
    import sys
    for field in xml_filter(sys.argv[1]):
        print field