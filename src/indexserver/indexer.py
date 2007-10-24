from __future__ import with_statement
import itertools
import logging
import os
import time
import threading

import setuppaths
import processing
import xappy

import dbspec
import flaxpaths
import util
import flax
import logclient
import doc_collection

try:
    import w32com_ifilter
    windows = True
except ImportError:
    windows = False

import simple_text_filter
import htmltotext_filter

log = logging.getLogger('indexing')


#util.setup_psyco()

class Indexer(object):
    """Perform indexing of a xapian database on demand.
    """

    def __init__(self):

        self._filter_map = {"Xapian": htmltotext_filter.html_filter,
                            "Text": simple_text_filter.text_filter}
        if windows:
            self._filter_map["IFilter"] =  w32com_ifilter.remote_ifilter

    def do_indexing(self, col, filter_settings, continue_check):

        """Perform an indexing pass.

        Index the database for col using filters given by
        filter_settings.  The filename is used as the document id, and
        this is used to remove documents in the database that no
        longer have an associated file.

        
        continue_check will be called before each file of the
        collection is about to be processed. If it returns False then
        indexing will stop and do_indexing will return False.

        If do_indexing attempt to index all the files then it will return True.
        
        """
        conn = None
        try:
            name = col.name
            log.info("Indexing collection: %s with filter settings: %s" % (name, filter_settings))
            dbname = col.dbpath()

            # This will error if the directory containing the databases has
            # disappeared, but that's probably a good thing - the document
            # collection is supposed to know where its database is - if it's
            # asking for indexing of a non-existent database, then it's the
            # collection's problem not the indexer's.
            # FIXME - we should really test for the error though, so we can
            # give a better error message.
            conn = xappy.IndexerConnection(dbname)
            
            docs_found = dict((id, False) for id in conn.iterids())

            error_count = file_count = 0
            for f in col.files():
                if not self._process_file(f, conn, name, filter_settings):
                    error_count += 1
                file_count += 1
                docs_found[f]=True
                if not continue_check(file_count, error_count):
                    return False
                conn.flush()

            for id, found in docs_found.iteritems():
                if not found:
                    log.info("Removing %s from %s" % (id, name))
                    conn.delete(id)
                    continue_check(file_count, error_count)

            log.info("Indexing of %s finished" % name)
            return True
            
        except xappy.XapianDatabaseLockError, e:
            log.error("Attempt to index locked database: %s, ignoring" % dbpath)
        except Exception, e:
            log.error("Unhandled error in do_indexing: %s" % str(e))
            import traceback
            traceback.print_exc()
            raise
        finally:
            if conn:
                conn.close()
                

    def _find_filter(self, filter_name):
        return self._filter_map[filter_name] if filter_name in self._filter_map else None

    def _accept_block(field_name, content):
        """Decide whether a block is acceptable for storing in a document.

        Blocks are rejected if their field name is one that Flax reserves for its internal use.

        """
        if field_name in dbspec.internal_fields():
            log.error("Filters are not permitted to add content to the field: %s, rejecting block" % field_name)
            return False
        else:
            return True

    def _process_file(self, file_name, conn, collection_name, filter_settings):
        """ Extract text from a file, make a xapian document and add
        it to the database. Return True if complete succesfully, False
        otherwise.
        """
        log.info("Indexing collection %s: processing file: %s" % (collection_name, file_name))
        unused, ext = os.path.splitext(file_name)
        ext = ext.lower()
        if self.stale(file_name, conn):
            filter = self._find_filter(filter_settings[ext[1:]])
            if filter:
                log.debug("Filtering file %s using filter %s" % (file_name, filter))
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
                    log.debug("Added (or replaced) doc %s to collection %s with text from source file %s" %
                                  (doc.id, collection_name, file_name))
                    return True
                except Exception, e:
                    log.error("Filtering file: %s with filter: %s raised exception %s, skipping"
                                   % (file_name, filter, e))
                    return False
            else:
                log.warn("Filter for %s is not valid, not filtering file: %s" % (ext, file_name))
                return False
        else:
            log.debug("File: %s has not changed since last indexing, not filtering" % file_name)
            return True

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
            log.error("Existing document %s has no mtime field" % doc.id)
            return True
        return rv


class IndexServer(processing.Process):
    """ The indexing process.  Controls a remote indexer and provides
    methods for interacting with it.

    Note that the logic for controlling the execution of the indexer
    all runs in the main process (the one creating the IndexServer
    object).
    """

    def __init__(self, logconfpath):
        processing.Process.__init__(self)
        self.setDaemon(True)
        self.logconfio = processing.Pipe()
        self.inpipe = processing.Pipe()
        self.outpipe = processing.Pipe()
        self.syncman = processing.LocalManager()
        self.error_count_sv = self.syncman.SharedValue('i',0)
        self.file_count_sv = self.syncman.SharedValue('i', 0)

        # Note that although this lock is only used in the main
        # process on windows instances of this class are pickled so we
        # have to use processing.Lock rather than threading.Lock. (On
        # linux threading.Lock is fine.)

        # changes to stop_sv and currently indexing should be atomic - use this lock to ensure so.
        self.state_lock = processing.Lock() 
        self.stop_sv = self.syncman.SharedValue('i', 0)
        self.currently_indexing = None

        self.hints = set()
        self.logconfpath = logconfpath
        self.start()

    def run(self):
        logclient.LogListener(self.logconfio[1]).start()
        logclient.LogConf(self.logconfpath).update_log_config()
        indexer = Indexer()
        while True:
            collection, filter_settings = self.inpipe[1].recv()
            self.outpipe[0].send(indexer.do_indexing(collection, filter_settings, self.continue_check))

    def continue_check(self, file_count, error_count):
        self.file_count_sv.value = file_count
        self.error_count_sv.value = error_count
        return not self.stop_sv.value
            
    def do_indexing(self, collection):
        assert not self.currently_indexing
        assert not self.stop_sv.value
        self.hints.discard(collection)
        collection.indexing_due = False
        self.currently_indexing = collection
        self.error_count_sv.value = 0
        self.file_count_sv.value = 0
        self.inpipe[0].send((collection, flax.options.filter_settings))
        # block here for a result
        # the return value shows whether we finished, or were prematurely stopped
        collection.indexing_due = not self.outpipe[1].recv()        
        collection.file_count = self.file_count_sv.value
        collection.error_count = self.error_count_sv.value
        with self.state_lock:
            self.stop_sv.value = False
            self.currently_indexing = None
                
    def async_do_indexing(self, collection):
        # call do_indexing in a separate thread and return.
        util.AsyncFunc(self.do_indexing)(collection)

    def indexing_info(self, collection):
        """ Returns a triple of indexing information for the collection updated in real time
        for an indexing collection, or the cached values from last indeding otherwise
        
        currently_indexing: True iff collection is currently indexing
        file_count: number of files 
        error_count: number of files that generate errors.
        """
        if collection is self.currently_indexing:
            return True, self.file_count_sv.value, self.error_count_sv.value
        else:
            return False, collection.file_count, collection.error_count

    def ok_to_index(self, collection):
        assert isinstance(collection, doc_collection.DocCollection)
        return collection.indexing_due and not collection.indexing_held

    def start_indexing(self, hint = None):
        """ Select a collection for indexing and start indexing
        it. Prefer the collection passed in hint (if any). If there is
        already a collection indexing do nothing.
        """
        assert not hint or isinstance(hint, doc_collection.DocCollection)
        if self.currently_indexing:
            if hint:
                if hint.indexing_due:
                    self.hints.add(hint)
                else:
                    self.hints.discard(hint)
            return

        for col in itertools.chain([hint] if hint else [], self.hints, flax.options.collections.itervalues()):
            if self.ok_to_index(col):
                self.async_do_indexing(col)
                break

    def stop_indexing(self, collection):
        """Stop indexing collection if it is currently indexing,
        otherwise do nothing"""
        
        with self.state_lock:
            if self.currently_indexing is collection:
                self.stop_sv.value = True
        # stopping collection might mean another can now be indexed..:
        self.start_indexing()

    def hold_indexing(self, collection):
        collection.indexing_held = True
        self.stop_indexing(collection)

    def unhold_indexing(self, collection):
        collection.indexing_held = False
        self.start_indexing(collection)

    def set_due(self, collection):
        collection.indexing_due = True
        self.start_indexing(collection)

    def unset_due(self, collection):
        collection.indexing_due = False
        self.start_indexing(collection)
        
    # convenience function
    def toggle_due_or_held(self, collection, held):
        assert isinstance(collection, doc_collection.DocCollection)
        if held:
            if collection.indexing_held:
                self.unhold_indexing(collection)
            else:
                self.hold_indexing(collection)
        else:
            if collection.indexing_due:
                self.unset_due(collection)
            else:
                self.set_due(collection)
