from __future__ import with_statement
import itertools
import logging
import os
import time

import sys
sys.path.append('..')
import setuppaths
import util

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

    def do_indexing(self, doc_col, filter_settings):
        """
        Index the database for doc_col using filters given by
        filter_settings. The filename is used as the document id, and
        this is used to remove documents in the database that no
        longer have an associated file.
        """
        try:
            self.log = logging.getLogger('indexing')
            self.log.info("Indexing collection: %s with filter settings: %s" % (doc_col.name, filter_settings))

            # This will error is the directory containing the
            # databases has disappeared, but that's probably a good
            # thing - the document collection is supposed to know
            # where it's database is - if it's asking for indexing of
            # a non-existent database, then it's the collection's
            # problem not the indexer's.
            conn = xappy.IndexerConnection(doc_col.dbname())
            
            docs_found = dict((id, False) for id in conn.iterids())

            for f in doc_col.files():
                self._process_file(f, conn, doc_col.name, filter_settings)
                docs_found[f]=True

            for id, found in docs_found.iteritems():
                if not found:
                    self.log.info("Removing %s from %s" % (id, doc_col.name))
                    conn.delete(id)
            self.log.info("Indexing of %s finished" % doc_col.name)
        except xappy.DatabaseLockError, e:
            self.log.error("Attempt to index locked database: %s, ignoring" % doc_col.dbname())
        except Exception, e:
            self.log.error("Unhandled error in do_indexing: %s" % str(e))
            import traceback
            traceback.print_exc()
        finally:
            conn.close()

    def _find_filter(self, filter_name):
        return self._filter_map[filter_name] if filter_name in self._filter_map else None

    def _accept_block(field_name, content):
        """ decide whether a block is acceptable for storing in a document.
        Blocks are rejected if their field name is one that Flax reserves for its internal use.
        """
        if field_name in ("filename", "collection", "mtime", "size"):
            self.log.error("Filters are not permitted to add content to the field: %s, rejecting block" % field_name)
            return False
        else:
            return True
        
    
    def _process_file(self, file_name, conn, collection_name, filter_settings):
        self.log.info("Indexing collection %s: processing file: %s" % (collection_name, file_name))
        _, ext = os.path.splitext(file_name)
        if self.stale(file_name, conn):
            filter = self._find_filter(filter_settings[ext[1:]])
            if filter:
                self.log.info("Filtering file %s using filter %s" % (file_name, filter))
                fixed_fields = ( ("filename", file_name),
                                 ("collection", collection_name),
                                 ("mtime", str (os.path.getmtime (file_name))),
                                 ("size", str (os.path.getsize (file_name))),
                               )
                try:
                    filtered_blocks = itertools.ifilter(self._accept_block, filter(file_name))
                    fields = itertools.starmap(xappy.Field, itertools.chain(fixed_fields, filtered_blocks))
                    doc = xappy.UnprocessedDocument(fields = fields)
                    doc.id = file_name
                    conn.replace(doc)
                except Exception, e:
                    self.log.error("Filtering file: %s with filter: %s raised exception %s, skipping"
                                   % (file_name, filter, e))
                    return
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
        return os.path.getmtime(file_name) != float(doc.data['mtime'][0])
