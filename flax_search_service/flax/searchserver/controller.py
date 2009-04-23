# Copyright (c) 2009 Lemur Consulting Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
r"""Controller for database creation and deletion, and modification threads.

This file contains all the code to manage creation, starting and stopping of
threads for modification of the database.

"""
__docformat__ = "restructuredtext en"

# Local modules
import backends
import utils

# Global modules
import os
import shutil
import threading
import wsgiwapi

def synchronised(fn):
    """Decorator to ensure that a call is only performed with the lock held.

    """
    def res(self, *args):
        self.mutex.acquire()
        try:
            fn(self, *args)
        finally:
            self.mutex.release()
    return res

class InfoFile(object):
    """Manage files containing details of a database.

    """
    def __init__(self, db_dir=None, backend_name=None, db_name=None):
        if db_dir is None:
            self.backend_name = backend_name
            self.db_name = db_name
        else:
            self.load(db_dir)

    def load(self, db_dir):
        """Load the information about a database from the specified path.

        """
        fd = open(os.path.join(db_dir, 'flaxinfo.txt'), "rb")
        try:
            self.backend_name, self.db_name = utils.json.loads(fd.read())
        finally:
            fd.close()

    def save(self, db_dir):
        """Save the information about a database to the specified path.

        """
        infopath = os.path.join(db_dir, 'flaxinfo.txt')
        tmppath = os.path.join(db_dir, 'flaxinfo.tmp')
        fd = open(tmppath, 'wb')
        try:
            fd.write(utils.json.dumps([self.backend_name, self.db_name]))
        finally:
            fd.close()
        os.rename(tmppath, infopath)

class Controller(object):
    def __init__(self, dbs_path, backend_settings, settings_db):
        """Set up the controller.

        """
        self.dbs_path = dbs_path
        self.backend_settings = backend_settings
        self.settings_db = settings_db

        # Lock which should be held when trying to create or delete a database,
        # or start or stop a database writer thread.
        self.mutex = threading.Lock()

        # Dictionary of writers for each database.
        self.writers = {}

    def db_names(self):
        """Get a list of the database names.

        """
        if not os.path.isdir(self.dbs_path):
            return []
        names = []
        infofile = InfoFile()
        for db_dir in os.listdir(self.dbs_path):
            db_dir = os.path.join(self.dbs_path, db_dir)
            try:
                infofile.load(db_dir)
            except ValueError:
                # Ignore databases for which the infofile is not readable, or
                # not present.
                continue

            try:
                backend = backends.get(infofile.backend_name,
                                       self.backend_settings)
            except wsgiwapi.HTTPError:
                # Ignore databases for which the backend is not available.
                continue

            names.append[infofile.db_name]
        names.sort()
        return names

    def get_path_and_backend(self, dbname):
        """Get the path to a named database, and the backend object for it.

        Raises an HTTPError if the database is not found, or the database
        backend does not exist.

        """
        db_dir = utils.dbpath_from_urlquoted(self.dbs_path, dbname)
        if not os.path.exists(db_dir):
            raise wsgiwapi.HTTPError(404, "Database not found")
        infofile = InfoFile(db_dir)
        backend = backends.get(infofile.backend_name, self.backend_settings)
        return os.path.join(db_dir, 'db'), backend

    def get_database(self, dbname, readonly):
        """Get a database object for the named database.

        Raises an HTTPError if the database is not found, or the database
        backend does not exist.

        The close() method of the returned database should be called after use.

        """
        dbpath, backend = self.get_path_and_backend(dbname)
        return backend.get_db(dbpath, readonly)

    def _stop_writer(self, dbname):
        """Stop the writer for the named database.

        The mutex must already be held by the current thread when this is
        called.

        """
        writer = self.writers.get(dbname)
        if writer is None:
            return
        FIXME # implement - stop the writer thread

    @synchronised
    def create_db(self, backend_name, dbname, overwrite, reopen):
        """Create a database.

         - `backend_name` is the name of the backend to use.
         - `dbname` is the name of the database.
         - `overwrite`, if True, causes the database to be deleted and
           recreated if the database already exists.
         - `reopen`, if True, causes the database to be left alone if it
           already exists.

        """
        db_dir = utils.dbpath_from_urlquoted(self.dbs_path, dbname)

        if os.path.exists(db_dir):
            if overwrite:
                # Delete the old database.
                self._stop_writer(dbname)
                infofile = InfoFile(db_dir)
                backend = backends.get(infofile.backend_name, self.backend_settings)
                backend.delete_db(os.path.join(db_dir, 'db'))
                shutil.rmtree(db_dir)
            elif reopen:
                return
            else:
                raise wsgiwapi.HTTPError(400, "Database, or some other file, already exists at specified location")

        try:
            os.mkdir(db_dir)
            infofile = InfoFile(backend_name=backend_name, db_name=dbname)
            backend = backends.get(backend_name, self.backend_settings)
            backend.create_db(os.path.join(db_dir, 'db'))
            infofile.save(db_dir)
        except:
            shutil.rmtree(db_dir)
            raise

    @synchronised
    def delete_db(self, dbname, allow_missing):
        """Delete a database.

        If `allow_missing` is true, do nothing if the database is missing.
        Otherwise, raise an error if the database is missing.

        """
        db_dir = utils.dbpath_from_urlquoted(self.dbs_path, dbname)
        if not os.path.exists(db_dir):
            if allow_missing:
                return
            raise wsgiwapi.HTTPError(400, "Database missing")
        self._stop_writer(dbname)
        try:
            infofile = InfoFile(db_dir)
            backend = backends.get(infofile.backend_name, self.backend_settings)
            backend.delete_db(os.path.join(db_dir, 'db'))
        finally:
            shutil.rmtree(db_dir)

    @synchronised
    def start_writer(self, dbname):
        """Start a writer for the named database.

        """
        writer = self.writers.get(dbname)
        if writer is not None:
            # Already exists
            FIXME # check that the writer is running ok
            return
        FIXME # implement - create and start the writer thread
