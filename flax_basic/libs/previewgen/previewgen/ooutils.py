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
import PythonMagickWand
from ctypes import c_size_t, pointer


class OOoImagePreviewer(object):
    """ Abstract base class providing a common framework for
    extracting preview images from documents with openoffice.

    """
    
    def __init__(self):
        self._wand = PythonMagickWand.NewMagickWand()

        self._odt_save_props = ( self.make_prop("FilterName", "writer8"), )
        pdf_filter_props =     ( self.make_prop("PageRange", "1"), )
        self._pdf_save_props = ( self.make_prop("FilterName", "writer_pdf_Export"),
                                 self.make_prop("FilterData", pdf_filter_props) )
        self._load_props = ( self.make_prop("Hidden", True), )

    _file_url_prefix = "file:///"
    def _filename_to_url(self, filename):
        filename = os.path.normpath(filename)
        filename = filename.replace("\\", "/")
        return self._file_url_prefix + filename

    def _load_document(self, infile):
        props = self._load_props
        infile_url = self._filename_to_url(infile)
        return self.desktop.loadComponentFromURL(
            infile_url ,"_blank", 0, props)

    def _save_document(self, document, outfile, save_props):
        rv = False
        outfile_url = self._filename_to_url(outfile)
        try:
            document.storeToURL(outfile_url, save_props)
            rv = True
        finally:
            document.close(True)
        return rv
     
    def _temp_filename(self, suffix=".odt"):
        return tempfile.mktemp(suffix=suffix)

    _thumbnail_path = 'Thumbnails/thumbnail.png'
    def _extract_thumb_from_odt(self, odt_file):
        z = zipfile.ZipFile(odt_file)
        imagefile = z.open(self._thumbnail_path)
        rv = imagefile.read()
        z.close()
        return rv

    def _pdf_to_image(self, pdf):
        PythonMagickWand.ClearMagickWand(self._wand)
        PythonMagickWand.MagickReadImage(self._wand, pdf)
        PythonMagickWand.MagickSetImageFormat(self._wand, "PNG")
        PythonMagickWand.MagickScaleImage(self._wand, 400, 500)
        image_file = self._temp_filename(suffix=".png")
        PythonMagickWand.MagickWriteImage(self._wand, image_file)
        with open(image_file, 'rb') as f:
            rv = f.read()
        os.remove(image_file)
        return rv

    def get_preview(self, infile):
        unused, ext = os.path.splitext(infile)
        ext = ext[1:]
        if(ext == 'pdf'):
            rv =  self._pdf_to_image(infile)
        else:
            doc = self._load_document(infile)
            if not doc:
                return False
            #tempfile = self._temp_filename(suffix=".odt")
            tempfile = self._temp_filename(suffix=".pdf")
            if not self._save_document(doc, tempfile, self._pdf_save_props):
                return False
            #rv =  self._extract_thumb_from_odt(tempfile)
            rv =  self._pdf_to_image(tempfile)
            if os.path.exists(tempfile):
                os.remove(tempfile)
        return rv
