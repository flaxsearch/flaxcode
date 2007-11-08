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
"""A filter to extract text from pdf files using pypdf"""

import pyPdf

def pdf_filter(filename):
    with open(filename, 'rb') as f:
        reader = pyPdf.PdfFileReader(f)
        if reader.isEncrypted:
            decrypted = reader.decrypt("")
            if not decrypted:
                # maybe raise an exception since we couldn't
                # get anything.
                return
        
        doc_info = reader.getDocumentInfo()
        yield 'title', doc_info.title
        for page in reader.pages:
            yield 'content', page.extractText()

if __name__ == '__main__':
    while 1:
        filename = raw_input("Input a filename: ")
        for block in pdf_filter(filename):
            print block
