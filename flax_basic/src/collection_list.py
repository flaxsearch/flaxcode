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
"""Manage the list of all collections known to flax.

"""
__docformat__ = "restructuredtext en"

import logging
import threading
import types
import time

import doc_collection
import flax
import persist
import search
import shutil
import util
import xappy
import xapian

log = logging.getLogger("collections")

class CollectionList(object):
    """A list of collections.

    """

    def __init__(self):
        self._collections = {}

        # Collections which have been marked as deleted, but not yet fully
        # removed.  Key is collection name, value is the collection path.
        self._collections_being_deleted = {}

        # Condition, must be held whenever _handle_count is manipulated, and
        # notified whenever a handle count decreases to 0.
        self._handle_count_condition = threading.Condition()

        # A dictionary holding the number of handles on each database.  Used to
        # stop databases in use being deleted before the process using them has
        # finished.
        self._handle_count = {}

    def get_search_connection(self, names):
        """Get a SearchConnection for a list of connections.

        :Parameters:
         - `names`: The name of a collection, or a sequence of names of
           collections.

        Returns a SearchConnection object.

        """
        if isinstance(names, types.StringTypes):
            names = (names,)
        assert(len(names) > 0)

        # FIXME - handle the case of a collection not being found more gracefully.
        col = self._collections[names[0]]
        result = xappy.SearchConnection(col.dbpath())
        log.debug('Search connection to %r opened' % (names[0],))

        # Add the remaining databases to the connection in Result.
        # FIXME - this should really be done by xappy.  Currently, we have to
        # access the internal _index object and use it directly - which only
        # works properly if all the collections have the same index properties.
        for name in names[1:]:
            col = self._collections[name]
            result._index.add_database(xapian.Database(col.dbpath()))
            log.debug('Added %r to search connection' % (name,))

        self._handle_count_condition.acquire()
        try:
            # Register the callback here.
            result.append_close_handler(self._search_connection_closed, names)

            # Now, increment the count of handles.
            for name in names:
                newcount = self._handle_count.get(name, 0) + 1
                self._handle_count[name] = newcount
                log.debug('New connection count for %r is %d' % (name, newcount))
        finally:
            self._handle_count_condition.release()

        return result

    def _search_connection_closed(self, path, names):
        """Callback, called when a search connection is closed.

        """
        self._handle_count_condition.acquire()
        try:
            for name in names:
                try:
                    newcount = self._handle_count[name] - 1
                    self._handle_count[name] = newcount
                    log.debug('Search connection to %r closed - new connection count is %d' % (name, newcount))
                    if newcount == 0:
                        self._handle_count_condition.notifyAll()
                except KeyError:
                    # The name of the connection wasn't known; shouldn't happen,
                    # but there's not much point in complaining.
                    log.warning('Got notification of closure of unknown connection %r (at %r)' %
                                (name, path))
        finally:
            self._handle_count_condition.release()

    def index_connection_opened(self, name):
        """Register that an index connection to the database is open.

        """
        self._handle_count_condition.acquire()
        try:
            newcount = self._handle_count[name] + 1
            self._handle_count[name] = newcount
            log.debug('Opened indexer connection to %r: new connection count is %d' % (name, newcount))
        finally:
            self._handle_count_condition.release()

    def index_connection_closed(self, name):
        """Register that an index connection to the database has closed.

        """
        self._handle_count_condition.acquire()
        try:
            try:
                newcount = self._handle_count[name] - 1
                self._handle_count[name] = newcount
                log.debug('Closed indexer connection to %r: new connection count is %d' % (name, newcount))
                if newcount == 0:
                    self._handle_count_condition.notifyAll()
            except KeyError:
                # The name of the connection wasn't known; shouldn't happen,
                # but there's not much point in complaining.
                log.warning('Got notification of closure of unknown indexer connection %r (at %r)' %
                            (name, path))
        finally:
            self._handle_count_condition.release()

    def to_dict(self):
        """Get a dictionary containing the details of the collections."""
        cols = {}
        for key, val in self._collections.iteritems():
            # FIXME - convert the collection to a dict, so we just store
            # the settings we want to be persistent.  Like so:
            # cols[key] = val.to_dict()
            cols[key] = val

        delcols = {}
        for key, val in self._collections_being_deleted.iteritems():
            delcols[key] = val
        
        result = {'collections': cols}
        if len(delcols) != 0:
            result['collections_being_deleted'] = delcols
        return result

    def from_dict(self, coldict):
        """Update the collection list from a dictionary."""
        # Note - this is currently only called at startup, so can assume the
        # _collections dict is empty.  Assert that this is so, for robustness
        # against future changes.
        assert(len(self._collections) == 0)

        for name, val in coldict['collections'].iteritems():
            # FIXME - convert the collection from a dict.  Like so:
            #col = doc_collection.DocCollection(name)
            #col.from_dict(val)
            # Instead of:
            col = val

            self._collections[name] = col
            self._handle_count[name] = 0

        pending_deletes = coldict.get('collections_being_deleted', {})
        for name, dbpath in pending_deletes.iteritems():
            self._collections_being_deleted[name] = dbpath
            self._handle_count[name] = 0
            util.AsyncFunc(self._wait_to_delete_database)((name, dbpath))

    def _delete_database_from_disk(self, dbpath):
        """Delete a database from disk, given its path.

        Returns True if the database was deleted successfully.

        Return False if the deletion failed: this probably means that some
        other process was accessing the database directory when we tried to
        delete it, or the permissions are wrong somehow.

        """
        try:
            shutil.rmtree(dbpath)
            return True
        except Exception, e:
            log.error("Failed to delete database at %r: %s" % (dbpath, str(e)))
        return False

    def _wait_to_delete_database(self, (name, dbpath)):
        """Wait until there are no handles on a database, then delete it."""
        self._handle_count_condition.acquire()
        try:
            log.debug("Waiting for all handles on database %r to be dropped" % name)
            while True:
                while self._handle_count[name] > 0:
                    self._handle_count_condition.wait()
                log.debug("Deleting database %r from disk (path was %r)" % (name, dbpath))
                if self._delete_database_from_disk(dbpath):
                    del self._collections_being_deleted[name]
                    del self._handle_count[name]
                    persist.data_changed.set()
                    log.debug("Deleted database %r from disk (path was %r)" % (name, dbpath))
                    return
                # Wait for a bit longer, then try the delete again.
                time.sleep(1)
        finally:
            self._handle_count_condition.release()

    def new_collection(self, name, **kwargs):
        """Create a new collection.

        Returns None if successful, otherwise returns an error message.

        """
        assert isinstance(name, types.StringType)
        if self._collections.has_key(name):
            return "The collection name is already in use"
        if self._collections_being_deleted.has_key(name):
            return "A collection of this name is currently being deleted"

        log.info("Creating new collection: %s" % name)
        col = doc_collection.DocCollection(name)
        self._collections[name] = col
        self._handle_count[name] = 0
        if 'formats' not in kwargs:
            kwargs['formats'] = flax.options.formats
        col.update(**kwargs)

    def remove_collection(self, name):
        assert isinstance(name, types.StringType)
        if self._collections.has_key(name):
            log.info("Deleting collection %s" % name)
            col = self._collections[name]
            dbpath = col.dbpath()
            self._collections_being_deleted[name] = dbpath
            del self._collections[name]
            util.AsyncFunc(self._wait_to_delete_database)((name, dbpath))
            persist.data_changed.set()
        else:
            log.error("Failed attempt to delete collection %s, which does not"
                      " exist" % name)

    def search(self, query=None, col_id=None, doc_id=None, cols=None, format=None,
               exact=None, exclusions=None, tophit=0, maxhits=10):
        """Perform a search.

        Either query or (col_id and doc_id) should be passed, the latter
        idicates a similarity search for the document identified by col_id and
        doc_id.

        """
        if not cols:
            cols = self._collections.keys()
        dbnames_to_search = [self._collections[col].name for col in cols]
        if doc_id and col_id:
            query = (self._collections[col_id], doc_id)
        if query or exact or exclusions:
            return search.search(query, exact, exclusions, format, dbnames_to_search, tophit, maxhits)
        else:
            return None

    @property
    def collection_names (self):
        return self._collections.keys()

    def __getitem__(self, key):
        return self._collections.__getitem__(key)

    def __setitem__(self, key, val):
        self._collections.__setitem__(key, val)

    def __contains__(self, key):
        return self._collections.__contains__(key)

    def __iter__(self):
        return self._collections.__iter__()

    def iterkeys(self):
        return self._collections.iterkeys()

    def iteritems(self):
        return self._collections.iteritems()

    def itervalues(self):
        return self._collections.itervalues()
