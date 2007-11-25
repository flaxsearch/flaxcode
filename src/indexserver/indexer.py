# Copyright (C) 2007 Lemur Consulting Ltd
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
"""Indexer, which runs in a separate process.

"""
from __future__ import with_statement
__docformat__ = "restructuredtext en"

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

# We use a different logger for the indexing process because there can
# be a problem with synchronizing IO if we e.g. use the same handlers
# from different processes. By using different loggers we can easily
# configure different handlers to avoid such problems.
# See http://code.google.com/p/flaxcode/issues/detail?id=134 for more
# discussion.


remote_log = logging.getLogger("indexing.remote")
control_log = logging.getLogger("indexing.control")

class DiskSpaceShortage(Exception):
    
    def __str__(self):
        return "Disk space below safe minimum for indexing"

class Indexer(object):
    """Perform indexing of a xapian database on demand.

       Indexing a collection can take some time, the objects
       error_count_holder, file_count_holder and stop_flag_holder can
       be used to interegate the state of the indexing. Each is
       assumed to have a value attribute, the first two will be set to
       the number of files processed and the number of files that
       error during the current indexing. The last will be
       periodically checked, and if it's value is true then indexing
       will terminate quickly (without processing all files).
    """

    minumum_disk_space = 500000000

    def __init__(self, file_count_holder, error_count_holder, stop_flag_holder):

        self._filter_map = {"Xapian": htmltotext_filter.html_filter,
                            "Text": simple_text_filter.text_filter}
        
        if windows:
            self._filter_map["IFilter"] =  w32com_ifilter.remote_ifilter

        self.file_count_holder = file_count_holder
        self.error_count_holder = error_count_holder
        self.stop_flag_holder = stop_flag_holder


    def continue_check(self, file_count, error_count):
        self.file_count_holder.value = file_count
        self.error_count_holder.value = error_count
        return not self.stop_flag_holder.value

    def disk_space_short(self, dir):
        """ Return True if the disk space available on the volume that ``dir`` is
        mounted on is low (i.e. less the minumum_disk_space) if it can
        be determined. It may be that we can not determine the disk
        space in which case False is returned, in which case it might
        be that disk space is low, but we are unable to determine
        that."""
        free_space = util.volume_space_free_for_current_user(dir)
        if free_space:
            return free_space < self.minumum_disk_space
        else:
            return False

    def do_indexing(self, col, filter_settings):
        """Perform an indexing pass.

        Index the database for col using filters given by
        filter_settings.  The filename is used as the document id, and
        this is used to remove documents in the database that no
        longer have an associated file.

        continue_check will be called before each file of the
        collection is about to be processed. If it returns False then
        indexing will stop and do_indexing will return False.  If
        do_indexing attempts to index all the files then it will
        return True.

        """
        conn = None
        try:
            name = col.name
            remote_log.info("Indexing collection: %s with filter settings: %s" % (name, filter_settings))
            dbname = col.dbpath()

            # This will error if the directory containing the databases has
            # disappeared, but that's probably a good thing - the document
            # collection is supposed to know where its database is - if it's
            # asking for indexing of a non-existent database, then it's the
            # collection's problem not the indexer's.
            # FIXME - we should really test for the error though, so we can
            # give a better error message.
            conn = xappy.IndexerConnection(dbname)
            conn.set_max_mem_use(max_mem_proportion = 0.1)

            docs_found = dict((id, False) for id in conn.iterids())

            error_count = file_count = 0
            for f in col.files():
                if self.disk_space_short(dbname):
                    # raise an exception rather than return False - we
                    # don't want to keep trying to index in this
                    # situation.
                    raise DiskSpaceShortage
                if not self._process_file(f, conn, name, filter_settings):
                    error_count += 1
                file_count += 1
                docs_found[f]=True
                if not self.continue_check(file_count, error_count):
                    remote_log.debug("Prematurely terminating indexing, stop flag is true")
                    return False

            for id, found in docs_found.iteritems():
                if not found:
                    remote_log.debug("Removing %s from %s" % (id, name))
                    conn.delete(id)

            remote_log.info("Indexing of %s finished" % name)
            conn.close()
            remote_log.debug("Changes to %s flushed" % name)
            return True

        except xappy.XapianDatabaseLockError, e:
            remote_log.error("Attempt to index locked database: %s, ignoring" % dbname)
        except Exception, e:
            import traceback
            tb = traceback.format_exc()
            remote_log.error("Unhandled error in do_indexing, traceback is: %s" % tb)
            raise

    def _find_filter(self, filter_name):
        return self._filter_map[filter_name] if filter_name in self._filter_map else None

    def _accept_block(field_name, content):
        """Decide whether a block is acceptable for storing in a document.

        Blocks are rejected if their field name is one that Flax reserves for its internal use.

        """
        if field_name in dbspec.internal_fields():
            remote_log.error("Filters are not permitted to add content to the field: %s, rejecting block" % field_name)
            return False
        else:
            return True

    def _process_file(self, file_name, conn, collection_name, filter_settings):
        """ Extract text from a file, make a xapian document and add
        it to the database. Return True if complete succesfully, False
        otherwise.
        """
        remote_log.debug("Indexing collection %s: processing file: %s" % (collection_name, file_name))
        unused, ext = os.path.splitext(file_name)
        ext = ext.lower()
        if self.stale(file_name, conn):
            filter = self._find_filter(filter_settings[ext[1:]])
            if filter:
                remote_log.debug("Filtering file %s using filter %s" % (file_name, filter))
                fixed_fields = ( ("filename", file_name),
                                 ("nametext", os.path.basename(file_name)),
                                 ("filetype", os.path.splitext(file_name)[1][1:]),
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
                    remote_log.debug("Added (or replaced) doc %s to collection %s with text from source file %s" %
                                  (doc.id, collection_name, file_name))
                    return True
                except Exception, e:
                    remote_log.error("Filtering file: %s with filter: %s raised exception %s, skipping"
                                   % (file_name, filter, e))
                    return False
            else:
                remote_log.warn("Filter for %s is not valid, not filtering file: %s" % (ext, file_name))
                return False
        else:
            return True

    def stale(self, file_name, conn):
        "Has the file named by file_name has changed since we last indexed it?"

        try:
            remote_log.debug("Checking if file %s needs (re)indexing" % file_name)
            doc = conn.get_document(file_name)
        except KeyError:
            # file not in the database, so has "changed"
            remote_log.debug("File %s has not yet been indexed" % file_name)
            return True
        try:
            rv =  os.path.getmtime(file_name) != float(doc.data['mtime'][0])
        except KeyError:
            remote_log.error("Existing document %s has no mtime field" % doc.id)
            return True
        remote_log.debug("File %s %s reindexing" % (file_name, "needs" if rv else "doesn't need"))
        return rv


# This process is a bit messy to deal with a problem with shutting
# down when running as a service on Windows. Ideally we'd just like to
# use setDaemonic(True) and allow the processing infrastructure to
# clean up for us. But that doesn't work because things registered
# with atexit never get called when running as a windows service.

# So we manually manage killing the process with a shared value, and
# ensure that we call process._exit_func before exiting so that our
# child (daemonic) processes can clean up.

# (I don't understand why using the process's stop method doesn't do
# what we want - I guess that the exception isn't raised either
# because we're catching it somewhere we shouldn't, because something
# blocks too long so it can't raise in a timely fashion, or there's
# some bug in processing. Should investigate further)

class IndexProcess(logclient.LogClientProcess):

    def __init__(self, kill_self, *indexer_args):
        logclient.LogClientProcess.__init__(self)
        self.kill_self = kill_self
        self.setStoppable(True)
        self.inpipe = processing.Pipe()
        self.outpipe = processing.Pipe()
        self.indexer_args = indexer_args
        self.start()

    def run(self):
        self.initialise_logging()
        try:
            try:
                indexer = Indexer(*self.indexer_args)
                while not self.kill_self.value:
                    # we poll with a timeout to allow for stopping the
                    # process, otherwise we can't check the kill_self
                    # if we're blocking in .recv()
                    if self.inpipe[1].poll(2):
                        collection, filter_settings = self.inpipe[1].recv()
                        self.outpipe[0].send(indexer.do_indexing(collection, filter_settings))
            except (SystemExit, KeyboardInterrupt), e:
                # This happens on normal process termination, just log it as
                # info.  Don't re-raise because we don't want it to be printed
                # to stderr, and we're about to exit anyway.
                remote_log.info("Indexer process terminating")
            except:
                # This process is about to exit, and there's no layer above us
                # to handle exceptions.  Therefore, we just log the error.  We
                # don't re-raise it because this would cause output to stderr,
                # and stderr doesn't exist in some of the contexts we run in.
                import traceback
                tb = traceback.format_exc()
                remote_log.critical('Unhandled exception in IndexerProcess.run(), traceback follows:\n %s' % tb)
        finally:
            remote_log.info("Cleaning up child processes of indexer")
            processing.process._exit_func() 


    # call do indexing in the remote process, block until return value is sent back
    def do_indexing(self, collection, filter_settings):
        self.inpipe[0].send((collection, filter_settings))
        return self.outpipe[1].recv()


class IndexServer(object):
    """ The index server, controls when collections are indexed and
    provides information about the state of the indexing process.
    """

    def __init__(self):
        self.syncman = processing.Manager()
        self.error_count_sv = self.syncman.SharedValue('i',0)
        self.file_count_sv = self.syncman.SharedValue('i', 0)
        # changes to stop_sv and currently_indexing should be atomic - use this lock to ensure so.
        self.state_lock = threading.Lock()
        self.stop_sv = self.syncman.SharedValue('i', 0)
        self.kill_indexer = self.syncman.SharedValue('i', 0)
        self.currently_indexing = None
        self.hints = set()
        self.indexing_process = IndexProcess(self.kill_indexer,
                                             self.file_count_sv,
                                             self.error_count_sv,
                                             self.stop_sv)
        control_log.info("Started the indexing process with pid: %d" % self.indexing_process.getPid())

    def stop(self):
        # in order to stop in a timely fashion if something is
        # currently indexing we prematurely stop the indexing process
        if self.currently_indexing:
            self.stop_sv.value = 1
        control_log.debug("Stopping indexing_process")
        self.kill_indexer.value = 1
        
    def join(self, timeout = None):
        control_log.debug("waiting to join indexing_process")
        self.indexing_process.join(timeout)

    def log_config_listener(self):
        "return a listener for log configuration changes in the remote indexing process"
        return self.indexing_process.logconfio[0]

    def do_indexing(self, collection):
        assert not self.stop_sv.value
        self.hints.discard(collection)
        collection.indexing_due = False
        self.currently_indexing = collection
        self.error_count_sv.value = 0
        self.file_count_sv.value = 0
        # block here for a result
        # the return value shows whether we finished, or were prematurely stopped
        collection.indexing_due = not self.indexing_process.do_indexing(collection, flax.options.filter_settings)
        collection.file_count = self.file_count_sv.value
        collection.error_count = self.error_count_sv.value
        with self.state_lock:
            self.stop_sv.value = False
            self.currently_indexing = None
        # now that we've finished we can see if there's another collection due for indexing
        self.start_indexing()
        
    def async_do_indexing(self, collection):
        # call do_indexing in a separate thread and return.  Must set
        # currently indexing here, otherwise tests in the main thread
        # might test it false before the thread has set it.
        assert not self.currently_indexing
        self.currently_indexing = collection
        util.AsyncFunc(self.do_indexing)(collection)

    def indexing_info(self, collection):
        """Get information about the status of indexing.

        Returns a triple of indexing information for the collection updated in
        real time for an indexing collection, or the cached values from last
        indeding otherwise

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
