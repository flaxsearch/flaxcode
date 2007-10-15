from __future__ import with_statement
import itertools
import logging
import os
import time

import setuppaths
import processing
import xappy

import sys
sys.path.append('..')
import dbspec
import flaxpaths
import util

try:
    import w32com_ifilter
    windows = True
except ImportError:
    windows = False

import simple_text_filter
import htmltotext_filter

util.setup_psyco()

class Indexer(object):
    """Perform indexing of a xapian database on demand.
    """

    def __init__(self):

        self._filter_map = {"Xapian": htmltotext_filter.html_filter,
                            "Text": simple_text_filter.text_filter}
        if windows:
            self._filter_map["IFilter"] =  w32com_ifilter.remote_ifilter

    def do_indexing(self, col_name, dbname, filter_settings, files, status):
        """Perform an indexing pass.

        Index the database for col_name using filters given by
        filter_settings.  The filename is used as the document id, and
        this is used to remove documents in the database that no
        longer have an associated file.  status is a proxy for a
        remote dictionary to inform the web server about the state of
        the indexer.
        """
        status['currently_indexing'] = "Indexing"
        status['number_of_files'] = 0
        conn = None
        try:
            self.log = logging.getLogger('indexing')
            self.log.info("Indexing collection: %s with filter settings: %s" % (col_name, filter_settings))

            # This will error if the directory containing the databases has
            # disappeared, but that's probably a good thing - the document
            # collection is supposed to know where its database is - if it's
            # asking for indexing of a non-existent database, then it's the
            # collection's problem not the indexer's.
            # FIXME - we should really test for the error though, so we can
            # give a better error message.
            conn = xappy.IndexerConnection(dbname)
            status['number_of_documents'] = conn.get_doccount()
            print status
            docs_found = dict((id, False) for id in conn.iterids())

            for f in files:
                self._process_file(f, conn, col_name, filter_settings, status)
                docs_found[f]=True
                status['number_of_files'] += 1

            for id, found in docs_found.iteritems():
                if not found:
                    self.log.info("Removing %s from %s" % (id, col_name))
                    conn.delete(id)
                    status['number_of_documents'] = conn.get_doccount()

            conn.flush()

            self.log.info("Indexing of %s finished" % col_name)
        except xappy.XapianDatabaseLockError, e:
            self.log.error("Attempt to index locked database: %s, ignoring" % dbname)
        except Exception, e:
            self.log.error("Unhandled error in do_indexing: %s" % str(e))
            import traceback
            traceback.print_exc()
        finally:
            status['currently_indexing'] = "Indexed"
            if conn:
                conn.close()

    def _find_filter(self, filter_name):
        return self._filter_map[filter_name] if filter_name in self._filter_map else None

    def _accept_block(field_name, content):
        """Decide whether a block is acceptable for storing in a document.

        Blocks are rejected if their field name is one that Flax reserves for its internal use.

        """
        if field_name in dbspec.internal_fields():
            self.log.error("Filters are not permitted to add content to the field: %s, rejecting block" % field_name)
            return False
        else:
            return True

    def _process_file(self, file_name, conn, collection_name, filter_settings, status):
        """ Extract text from a file, make a xapian document and add
        it to the database.
        """
        self.log.info("Indexing collection %s: processing file: %s" % (collection_name, file_name))
        unused, ext = os.path.splitext(file_name)
        ext = ext.lower()
        if self.stale(file_name, conn):
            filter = self._find_filter(filter_settings[ext[1:]])
            if filter:
                self.log.debug("Filtering file %s using filter %s" % (file_name, filter))
                fixed_fields = ( ("filename", file_name),
                                 ("nametext", os.path.basename(file_name)),
                                 ("collection", collection_name),
                                 ("mtime", str(os.path.getmtime(file_name))),
                                 ("size", str(os.path.getsize(file_name))),
                               )
                for field, value in fixed_fields:
                    assert(field in dbspec.internal_fields())
                try:
                    filtered_blocks = itertools.ifilter(self._accept_block, filter(file_name))
                    fields = itertools.starmap(xappy.Field, itertools.chain(fixed_fields, filtered_blocks))
                    doc = xappy.UnprocessedDocument(fields = fields)
                    doc.id = file_name
                    conn.replace(doc)
                    status['number_of_documents'] = conn.get_doccount()
                    self.log.debug("Added (or replaced) doc %s to collection %s with text from source file %s" %
                                  (doc.id, collection_name, file_name))
                except Exception, e:
                    self.log.error("Filtering file: %s with filter: %s raised exception %s, skipping"
                                   % (file_name, filter, e))
            else:
                self.log.warn("Filter for %s is not valid, not filtering file: %s" % (ext, file_name))
        else:
            self.log.debug("File: %s has not changed since last indexing, not filtering" % file_name)

    def stale(self, file_name, conn):
        "Has the file named by file_name has changed since we last indexed it?"

        try:
            doc = conn.get_document(file_name)
        except KeyError:
            # file not in the database, so has "changed"
            return True
        try:
            rv =  os.path.getmtime(file_name) != float(doc.data['mtime'][0])
        except KeyError:
            self.log.error("Existing document %s has no mtime field" % doc.id)
            return True
        return rv

def index_server_loop(indexingio, logconfio, logconf_path):
    import logclient
    logclient.LogListener(logconfio)
    logclient.LogConf(logconf_path).update_log_config()
    indexer = Indexer()
    while True:
        args=indexingio.recv()
        indexer.do_indexing(*args)

class IndexServer(object):
    """ Manages the indexing of Flax databases in a child process and
    provides information about the state of collection indexing.
    """
    def __init__(self):
        self.logconfio = processing.Pipe()
        self.indexingio = processing.Pipe()
        self.syncman = processing.Manager()
        self.status_dict = dict()
        server = processing.Process(target=index_server_loop,
                                    name="IndexServer",
                                    args=(self.indexingio[1],
                                          self.logconfio[1],
                                          flaxpaths.paths.logconf_path))
        server.setDaemon(True)
        server.start()

    def maybe_initialise_status(self, col):
        if col.name not in self.status_dict:
            search_conn = col.search_conn()
            d = self.syncman.dict()

            d['currently_indexing'] = "Unknown"
            d['number_of_documents'] = search_conn.get_doccount()
            d['number_of_files'] = -1
            self.status_dict[col.name] = d


    def do_indexing(self, col, filter_settings):
        self.maybe_initialise_status(col)
        self.indexingio[0].send((col.name,
                                 col.dbname(),
                                 filter_settings,
                                 list(col.files()),
                                 self.status_dict[col.name]))

    @property
    def logconf_input(self):
        return self.logconfio[0]

    def get_status(self, col):
        """Returns the status of the indexing for the collection supplied.

        This is initialised from static information about the
        collection and then the indexer updates this information
        whilst it's running for a given collection

        The value is a dictionary with keys and values as follows:

         - currently_indexing: A string that describes what the
           indexer is doing, or has done, with this collection.

         - number_of_documents: The number of documents in the collection.

         - number_of_files: The number of source files for documents in the
           collection.  If currently_indexing is true this is the number of
           files that we have tried to index so far. If the currently_indexing
           is False it is the total considered at the last indexing run. Note
           the number_of_files can exceed number_of_documents, since (e.g.)
           corrupt files might not be added to the database.

        """
        self.maybe_initialise_status(col)
        return self.status_dict[col.name]
