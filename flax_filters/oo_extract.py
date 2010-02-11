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

# This depends on an openoffice being available to convert things on
# localhost:8100 start with e.g.:
# openoffice.org -accept="socket,host=localhost,port=8100;urp;" -invisible -headless
# startoo.bat has an example of how to do this on Windows

# tested with Open Office 3.0

import cStringIO
import logging
import time
import traceback
import os
import multiprocessing

import uno
from unohelper import Base, systemPathToFileUrl
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException
from com.sun.star.lang import DisposedException
from com.sun.star.io import IOException, XOutputStream

import path
import utils

connection_warning = """ failed to connect to openoffice with \
connection string {connect}, retrying in {interval} seconds.
"""


def get_oo_desktop(logger, port=8100):
    tmpl = "uno:socket,host=localhost,port={port},tcpNoDelay=1;urp;StarOffice.ComponentContext"
    connection_string = tmpl.format(port=port)
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext(
        "com.sun.star.bridge.UnoUrlResolver", local)
    interval = 0.0
    increment = 0.1
    limit = 2
    desktop = None
    while not desktop and interval < limit:
        try:
            context = resolver.resolve(connection_string)
            desktop = context.ServiceManager.createInstanceWithContext(
                'com.sun.star.frame.Desktop', context)
        except NoConnectException:
            next_interval = interval + increment
            logger.warning(connection_warning.format(
                    interval = next_interval,
                    connect = connection_string))
            time.sleep(interval)
            interval = next_interval
    return desktop

class OutputStream( Base, XOutputStream ):

    def __init__( self, ostream ):
        self.closed = 0
        self.ostream = ostream

    def closeOutput(self):
        self.closed = 1

    def writeBytes( self, seq ):
        self.ostream.write( seq.value )

    def flush( self ):
        pass

class OOextracter(object):

    def __init__(self, port=8100):
        # Since we will run under multiprocessing we need to use a different logger
        self.logger = multiprocessing.log_to_stderr()
        #self.logger = multiprocessing.get_logger()
        self.logprefix = "oo_extract." + str(port) + " : "
        self.logger.setLevel(logging.NOTSET)
        
        self.logger.debug(self.logprefix + "initialising new OOextracter")
        self.port = port
        self.get_desktop()
        self._load_props = ( self.make_prop("Hidden", True), )
        self._common_out_props = (
            self.make_prop("FilterFlags", "UTF-8"),
            )
        self._text_out_props = (
            (self.make_prop("FilterName", "Text (Encoded)"),) +
            self._common_out_props)

        self._csv_out_props = (
            (self.make_prop("FilterName", 'Text - txt - csv (StarCalc)'),) +
            self._common_out_props)

        self._html_out_props = (
            (self.make_prop("FilterName", 'impress_html_Export'),) +
            self._common_out_props)

        self._output_map = {
            "application/msword": self._text_out_props,
            "application/vnd.oasis.opendocument.text": self._text_out_props,
            
            "application/vnd.ms-excel" : self._csv_out_props,
            "application/vnd.oasis.opendocument.spreadsheet" : self._csv_out_props,

            "application/vnd.ms-powerpoint": self._html_out_props,
            "application/vnd.oasis.opendocument.presentation Open Office Impress": self._html_out_props,

            }

    def make_prop(self, name, value):
        prop = PropertyValue()
        prop.Name = name
        if isinstance(value, (list, tuple)):
            prop.Value = uno.Any("[]com.sun.star.beans.PropertyValue", value)
        else:
            prop.Value = value
        return prop
    
    def _filename_to_url(self, filename):
        # filename should be absolute.
        return systemPathToFileUrl(os.path.abspath(filename))

    def get_desktop(self):
        self.desktop = get_oo_desktop(self.logger, self.port)

    def _load_document(self, infile):
        props = self._load_props
        infile_url = self._filename_to_url(infile)
        try:
            return self.desktop.loadComponentFromURL(
                infile_url ,"_blank", 0, props)
        except DisposedException:
            self.logger.error(self.logprefix + "Disposed on loading: " + infile)
            self.get_desktop()

    def _unload_document(self, doc):
        try:
            doc.close(True)
        except DisposedException:
            self.logger.error(self.logprefix + 'Disposed on closing: FIXME doc name here')
            self.get_desktop()

    def _doc_text_to_stream(self, doc, contentstream, filename, mimetype):
        outprops = self._output_map.get(mimetype, self._text_out_props)
        outprops = (
             (self.make_prop("OutputStream", OutputStream(contentstream)),) +
            outprops)
        try:
            doc.storeToURL("private:stream", outprops)
        except IOException:
            self.logger.error(self.logprefix + "IOException, on storing, file is :" + 
                          filename)
            self.logger.debug(self.logprefix + traceback.format_exc())
    
    def __call__(self, filename, mimetype):
        # FIXME: We want to do more - e.g.  yield text in
        # e.g. paragraph blocks.
        if not self.desktop:
            self.get_desktop()
        doc = self._load_document(filename)
        if not doc:
            self.logger.error(self.logprefix + "oo conversion - couldn't load file: " + filename)
            yield "textcontent", ""
        else:
            props = doc.DocumentProperties
            yield "author",  props.Author
            # FIXME: how do we iterate over this?
            # yield "keyword", props.Keywords
            yield "title", props.Title
            yield "description", props.Description
            yield "subject", props.Subject
            contentstream = cStringIO.StringIO()
            self._doc_text_to_stream(doc, contentstream, filename, mimetype)
            yield "textcontent", contentstream.getvalue()
            self._unload_document(doc)
