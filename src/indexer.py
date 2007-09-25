from __future__ import with_statement
import itertools
import os

import filespec
import util
util.setup_sys_path()

import xappy

try:
    import w32com_ifilter
    windows = True
except ImportError:
    windows = False

import simple_text_filter

util.setup_psyco()

class Indexer(object):
    """ Perform indexing of a xapian database on demand.  The indexing
        process might be fragile since we're potentially invoking
        third party filters that may fall over or fail to terminate.
    """
    
    def __init__(self):
        self._filter_map = {"Xapian": None,
                            "Text": simple_text_filter.text_filter}
        if windows:
            self._filter_map["IFilter"] =  w32com_ifilter.ifilter_filter

    def do_indexing(self, file_spec, dbname, filter_settings):
        """
        Index the database dbname with files given by file_spec
        using filters given by filter_settings.
        """
        print "Indexing xapian db: %s,\n with files from filespec %s\n filter settings: %s" % (dbname, file_spec, filter_settings)
        conn = xappy.IndexerConnection(dbname)
        for f in file_spec.files():
            self._process_file(f, conn, filter_settings)
        conn.close()
        print "Indexing Finished"

    def _find_filter(self, filter_name):
        return self._filter_map[filter_name] if filter_name in self._filter_map else None
    
    def _process_file(self, file_name, conn, filter_settings):
        print "processing file: ", file_name
        _, ext = os.path.splitext(file_name)
        filter = self._find_filter(filter_settings[ext[1:]])
        if filter:
            fields = itertools.starmap(xappy.Field, filter(file_name))
            conn.add(xappy.UnprocessedDocument(fields = fields))
        else:
            print "filter for %s is not valid" % ext
