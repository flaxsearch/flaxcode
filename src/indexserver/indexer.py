from __future__ import with_statement
import itertools
import logging
import os
import time

import sys
sys.path.append('..')
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
        self.log = logging.getLogger('indexing')
        self._filter_map = {"Xapian": None,
                            "Text": simple_text_filter.text_filter}
        if windows:
            self._filter_map["IFilter"] =  w32com_ifilter.ifilter_filter

    def do_indexing(self, doc_col, filter_settings):
        """
        Index the database for doc_col using filters given by
        filter_settings. The filename is used as the document id, and
        this is used to remove documents in the database that no
        longer have an associated file.
        """
        self.log.info("Indexing collection: %s with filter settings: %s" % (doc_col.name, filter_settings))
        conn = xappy.IndexerConnection(doc_col.dbname())

        docs_found = dict((id, False) for id in conn.iterids())
        
        for f in doc_col.files():
            self._process_file(f, conn, doc_col.name, filter_settings)
            docs_found[f]=True

        for id, found in docs_found.iteritems():
            if not found:
                self.log.info("Removing %s from %s" % (id, doc_col.name))
                conn.delete(id)

        conn.close()
        self.log.info("Indexing of %s finished" % doc_col.name)


    def _find_filter(self, filter_name):
        return self._filter_map[filter_name] if filter_name in self._filter_map else None
    
    def _process_file(self, file_name, conn, collection_name, filter_settings):
        self.log.info("Indexing collection %s: processing file: %s" % (collection_name, file_name))
        _, ext = os.path.splitext(file_name)
        if self.stale(file_name, conn):
            filter = self._find_filter(filter_settings[ext[1:]])
            if filter:
                log.info("Filtering file %s using filter %s" % (file_name, filter))
                fixed_fields = ( ("filename", file_name),
                                 ("collection", collection_name),
                                 ("mtime", str(time.time())))
                fields = itertools.starmap(xappy.Field, itertools.chain(fixed_fields, filter(file_name)))
                doc = xappy.UnprocessedDocument(fields = fields)
                doc.id = file_name
                conn.replace(doc)
            else:
                self.log.warn("Filter for %s is not valid, not filtering file: %s" % (ext, file_name))
        else:
            self.log.info("File: %s has not changed since last indexing, not filtering" % file_name)

    def stale(self, file_name, conn):
        "Return True if the file named by file_name has changed since we indexed it last"

        try:
            doc = conn.get_document(file_name)
        except KeyError:
            # file not in the database, so has "changed"
            return True

        # This will error if the mtime field isn't in the document
        # with appropriate data, but that shouldn't happen because
        # every document should have mtime data of the correct format.
        # So let the exception through in order to diagnose the
        # problem.  We are potentially vunerable to a filter that adds
        # things with that field, but the restriction is documented.
        return os.path.getmtime(file_name) > float(doc.data['mtime'][0])
