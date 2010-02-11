#!/usr/bin/python2.6
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
import os
import itertools
import json
import logging
import sys
import time
import traceback
import fileinput
import glob

import path
import utils
import extract

def get_extracters(process_num):
    return (
        # we rely on this being first so that we can get the filename easily
        extract.filepath,
        extract.content_extracter(process_num),
        extract.filetype,
        extract.file_stats,
        )

def unicode_filter(it, logger, ignored=set(('acl',))):
    """
    Turns all field/value pairs into Unicode except the ones flagged to ignore
    """
    for f, v in it:
        if v is None:
            message = "field {field} has null data, skipping".format(field=f)
            logger.warning(message)
        else:
            decoded = v
            if (f not in ignored) and isinstance(v, str):
                decoded = v.decode('utf8', 'ignore')
            yield f, decoded

def make_dir_if_needed(filename,outpath):
    """
    Makes a directory if needed for output
    """
    if outpath != "":
        if os.path.isdir(filename):
            if filename.startswith('\\'):
                filename = filename[1:]
            outdir = os.path.join(outpath,filename)
            if not os.path.isdir(outdir):
                os.makedirs(outdir)

def process_file(filename, extracters, logger, outdir):
    """
    Process a file and output it to JSON
    """
    try:
        logger.info('starting to process file: ' + filename)
        extracted = itertools.chain(* (e(filename) for e in extracters))
        # ensure that it's unicoded:
        extracted = list(unicode_filter(extracted, logger))
        # this relies on filepath being the first thing
        filename = extracted[0][1]
        # this relies on the mtime being the last thing
        mtime = extracted[-1][1]
        if filename.startswith('\\'):
            filename = filename[1:]
        record_file = os.path.join(outdir, filename) + ".json"
        with open(record_file, 'wb') as f:
            json.dump(extracted, f)
        logger.info('finished processing file: ' + filename)
        return True
    except:
        try:
            templ = "processing file {file}\nUncaught Exception: {trace}"
            msg = templ.format(file=filename,
                               trace=traceback.format_exc())
            logger.error(msg)
            return False
        except:
            logger.error(
                "error preparing exception traceback for file: " + filename)
            return False

            
def process_dir(filename, extracters, logger, outpath):
    """
    Process a dir of files recursively
    """
    make_dir_if_needed(filename,outpath)
    for currentFile in glob.glob( os.path.join(filename, '*') ):
        if os.path.isdir(currentFile):
            # make sure output dirs exist
            process_dir(currentFile, extracters, logger, outpath)
        else:
            process_file(currentFile, extracters, logger, outpath)

            
if __name__ == "__main__":
    """
    Extract a file or files in a directory to JSON. If 
    a output directory is specified then the structure of any
    input directory will be appended to this.
    """
    utils.initialise_logging()
    utils.fixup_ooo_environ()
    # extract.py allows for multiple extracters to run in multiple processes, but we don't use this:
    process_num = 0
    extracters = get_extracters(process_num)
    logger = logging.getLogger("extract." + str(process_num))
    if len(sys.argv) < 2:
        print "\nUsage:\n\nextract_to_json.py <file or directory> <output directory>\n\n"
        sys.exit()
    infile = sys.argv[1]
    if len(sys.argv) > 2:
        outdir = sys.argv[2] + "\\"
    else:
        outdir = ""
    if os.path.isdir(infile):
        process_dir(infile, extracters, logger, outdir)
    else:
        process_file(infile, extracters, logger, outdir)
    



    
