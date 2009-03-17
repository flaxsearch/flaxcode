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

"""
__docformat__ = "restructuredtext en"

import os
import shutil
import threading
import xappy
import wsgiwapi

def synchronised(fn):
    """Decorator to ensure that a call is only performed with the 

    """
    def res(self, *args):
        self.mutex.acquire()
        try:
            fn(self, *args)
        finally:
            self.mutex.release()
    return res

class Controller(object):
    def __init__(self, dbs_path, settings_db):
        """Set up the controller.

        """
        self.dbs_path = dbs_path
        self.settings_db = settings_db

        # Lock which should be held when trying to create or delete a database,
        # or start or store a database writer thread.
        self.mutex = threading.Lock()

        # Dictionary of writers for each database.
        self.writers = {}

    def _stop_writers(self, dbname):
        writer = self.writers.get(dbname)
        if writer is None:
            return
        FIXME # implement

    @synchronised
    def create_db(self, dbname, overwrite, reopen):
        """Create a database.

        """
        dbpath = os.path.join(self.dbs_path, dbname)
        if os.path.exists(dbpath):
            if overwrite:
                self._stop_writers(dbname)
                shutil.rmtree(dbpath)
            elif not reopen:
                raise wsgiwapi.HTTPError(400, "Database already exists")
        xappy.IndexerConnection(dbpath)

    @synchronised
    def delete_db(self, dbname, allow_missing):
        dbpath = os.path.join(self.dbs_path, dbname)
        if not os.path.exists(dbpath):
            if allow_missing:
                return
            raise wsgiwapi.HTTPError(400, "Database missing")
        self._stop_writers(dbname)
        shutil.rmtree(dbpath)
