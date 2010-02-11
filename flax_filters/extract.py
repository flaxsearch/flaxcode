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

import mimetypes
import os
import time
import logging

import utils
import path
import html_extract
import external_extract

if not utils.is_windows():
    import grp
    import pwd

# maps mime_types to user friendly names
mimetype_filetypes = {
    # plain text formats
    "text/plain" : "text",
    "text/css" : "css",
    "text/xml" : "xml",
    
    # word office formats
    "application/msword" : "MS Word",
    "application/vnd.ms-excel" : "MS Excel",
    "application/vnd.ms-powerpoint" : "MS Powerpoint",
    
    # openoffice native formats
    "application/vnd.oasis.opendocument.text" : "OO Writer",
    "application/vnd.oasis.opendocument.spreadsheet": "OO Calc",
    "application/vnd.oasis.opendocument.presentation Open Office Impress" : "OO Impress",

    # pdf
    "application/pdf": "PDF",

    # html
    "application/xhtml+xml": "XHTML",
    "text/html": "HTML",
    }
    
# for types not in Python's mimetypes module
mimetypes_extratypes = {
    ".odt" : "application/vnd.oasis.opendocument.text", # Why is this not in mimetypes??
    }

logger = logging.getLogger()

def filepath(filename):
    yield "filepath", filename

def guess_mimetype(filename):
    s = mimetypes.guess_type(filename);
    if s[0] == None:
        s = (mimetypes_extratypes.get(os.path.splitext(filename)[1]), None)
    return s

def filetype(filename):
    mimename = guess_mimetype(filename)[0]
    yield "filetype", mimetype_filetypes.get(mimename, mimename)

def file_stats(filename):
    stats = os.stat(filename)
    
    if os.name == "posix":
        owner = pwd.getpwuid(stats.st_uid).pw_name
        yield "owner", owner
        
    yield "size", stats.st_size
    yield "ctime", stats.st_ctime
    yield "creation_year", time.gmtime(stats.st_ctime).tm_year

def text_file(filename, mimetype=None):
    with open(filename) as f:
        yield "textcontent", f.read()

def pdf2text(filename, mimetype=None):
    return external_extract.pdftotext_filter(filename)

def html2text(filename, mimetype=None):
    return html_extract.html_filter(filename)
    
def antiword2text(filename, mimetype=None):
    return external_extract.antiword_filter(filename)

def content(filename,cmap):
    # check whether we can read the file - no point trying to get
    # content if we can't
    if not os.access(filename, os.R_OK):
        logger.warning(
            "{fname} cannot be read - no content extracted".format(
                fname=filename))
        return ()
    
    mime_type, encoding = guess_mimetype(filename)
    
    ex = cmap.get(mime_type, None)
    if ex and not encoding:
        return ex(filename, mime_type)
    else:
        templ = "No suitable content extractor for {file}. ({mime}, {encoding})"
        logger.warning(templ.format(file=filename,
                                    mime=mime_type,
                                    encoding=encoding))
        return ()

def ooex_maker(portnum):
    import oo_extract
    return oo_extract.OOextracter(portnum)
        
def content_extracter(process_num=0):
    """
    Extracts the content from a file, by either:
    - running a simple function in this file (i.e. text_file)
    - running a function in another file (i.e. html2text)
    - running a command-line tool using external_extract (i.e. pdf2text)
    - running Open Office in a remote process (using an optional supplied process number)
    """
   
    portnum = process_num+8100;
    oo_ex = utils.RemoteFilterRunner(ooex_maker, portnum, cleanup=utils.kill_oo_by_port)
    
    def html_oo_ex(filename, mimetype):
        # for some filetypes oo will not save in a plain text format.
        # we deal with those by saving as html and then filtering the html:
        html_extracted = oo_ex(filename, mimetype)
        for k, v in html_extracted:
            if k == "textcontent":
                html_converted = html_extract.html_filter_from_stream(v)
                for kk, vv in html_converted:
                    yield kk, vv
            else:
                yield k, v
        
    cmap = {

        # plain text formats
        "text/plain" : text_file,
        "text/css" : text_file,
        "text/xml" : text_file,

        # word office formats
        "application/msword" : oo_ex,
        "application/vnd.ms-excel" : oo_ex,
        "application/vnd.ms-powerpoint" : html_oo_ex,

        # openoffice native formats
        "application/vnd.oasis.opendocument.text" : oo_ex,
        "application/vnd.oasis.opendocument.spreadsheet": oo_ex,
        "application/vnd.oasis.opendocument.presentation Open Office Impress" : html_oo_ex,

        # pdf
        "application/pdf": pdf2text,

        # html
        "application/xhtml+xml": html2text,
        "text/html": html2text
    }
    return lambda filename: content(filename,cmap)

    