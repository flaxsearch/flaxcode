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
import zipfile
import subprocess
import tempfile

import uno
from com.sun.star.beans import PropertyValue

# this depends on an openoffice being available to convert things on localhost:8100
# start with e.g.
# openoffice.org -accept="socket,host=localhost,port=8100;urp;" -invisible -headless

def filename_to_url(filename):
    return "file://" + filename

def convert_file_to_oo(infile, outfile):
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    context = resolver.resolve(
        "uno:socket,host=localhost,port=8100;urp;StarOffice.ComponentContext")
    desktop = context.ServiceManager.createInstanceWithContext(
        "com.sun.star.frame.Desktop", context)

    # the above stuff probably only needs to be done once - should be
    # cached somewhere.

    document = desktop.loadComponentFromURL(
        filename_to_url(infile) ,"_blank", 0, ())

    props = (PropertyValue("FilterName", 0, "writer8", 0),)
    document.storeToURL(filename_to_url(outfile), props)

def make_doc_preview_oo(filename, width, height):
    unused, temp = tempfile.mkstemp(suffix=".odt")
    convert_file_to_oo(filename, temp)
    z = zipfile.ZipFile(temp)
    p = z.open('Thumbnails/thumbnail.png')
    return p.read()

preview_maker_map = {'doc' : make_doc_preview_oo,
                     'html' : make_doc_preview_oo}

def make_preview(filename, width=100, height=100):
    unused, ext = os.path.splitext(filename)
    ext = ext[1:]
    try:
        return preview_maker_map[ext](filename, width, height)
    except KeyError:
        return None
