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

import os
import tempfile
import zipfile

class OOoImagePreviewer(object):
    """ Abstract base class providing a common framework for
    extracting preview images from documents with openoffice.

    """
    
    def _make_props(self, prop_pairs):
        return tuple([self.make_prop(*pair) for pair in prop_pairs])

    _file_url_prefix = "file:///"
    def _filename_to_url(self, filename):
        filename = os.path.normpath(filename)
        filename = filename.replace("\\", "/")
        return self._file_url_prefix + filename

    _load_props = (("Hidden", True),)
    def _load_document(self, infile):
        props = self._make_props(self._load_props)
        infile_url = self._filename_to_url(infile)
        return self.desktop.loadComponentFromURL(
            infile_url ,"_blank", 0, props)

    _save_props = (("FilterName", "writer8"),)
    def _save_document_as_odt(self, document, outfile):
        props = self._make_props(self._save_props)
        outfile_url = self._filename_to_url(outfile)
        document.storeToURL(outfile_url, props)
        document.close(True)
        return True
     
    def _temp_filename(self):
        return tempfile.mktemp(suffix=".odt")

    _thumbnail_path = 'Thumbnails/thumbnail.png'
    def _extract_thumb_from_odt(self, odt_file):
        z = zipfile.ZipFile(odt_file)
        imagefile = z.open(self._thumbnail_path)
        rv = imagefile.read()
        z.close()
        return rv

    def get_preview(self, infile):
        doc = self._load_document(infile)
        if not doc:
            return False
        tempfile = self._temp_filename()
        if not self._save_document_as_odt(doc, tempfile):
            return False
        rv =  self._extract_thumb_from_odt(tempfile)
        if os.path.exists(tempfile):
            os.remove(tempfile)
        return rv
     
