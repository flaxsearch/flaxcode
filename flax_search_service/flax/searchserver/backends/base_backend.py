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
"""Base class for backends.

"""
__docformat__ = "restructuredtext en"

class BaseBackend(object):
    """The base class for backends.

    This should be subclassed by each backend.  One instance of the subclass
    for each backend will be created.

    """
    def __init__(self, settings):
        """Initialise the backend.

         - `settings` contains a dictionary of settings specific to this
           backend to use.

        """
        self.settings = settings

    def version_info(self):
        """Return a string giving version information about the backend.

        The string is intended to be human readable - it need not be in any
        particular format.

        """
        raise NotImplementedError

    def create_db(self, db_path):
        """Create a database at db_path.

        `db_path` is an absolute path.

        When this is called, the parent directory of db_path will exist, but
        db_path will not.  Therefore, this function is at liberty to create
        whatever type of database is desired.  For backends which don't store
        data directly in the filesystem, the appropriate action is probably to
        create a file containing details of how to access the database.

        """
        raise NotImplementedError

    def delete_db(self, db_path):
        """Delete the database at db_path.

        When this is called, any writers for the specified database will
        already have been stopped.

        If any files are left under db_path when this returns, they will be
        cleaned up automatically.  The subclass is only responsible for any
        other cleanup which is required (eg, telling a remote server to delete
        the database).

        """
        raise NotImplementedError

    def get_db_reader(self, base_uri, db_path, readonly):
        """Get a DB Reader object, used for all read access to the database.

        The DB object can be newly allocated, or allocated from a pool.

        """
        raise NotImplementedError

    def get_db_writer(self, base_uri, db_path, readonly):
        """Get a DB Writer object, used for all write access to the database.

        This will generally be a singleton, and will implement backend writes
        in a separate thread.

        What should be returned if this is called multiple times?

        """
        raise NotImplementedError

class BaseDbReader(object):
    """Base class for databases returned by BaseBackend.get_db_reader().

    """
    def __init__(self, base_uri, db_path):
        """Create a database reader for the specified path.

        """
        self.base_uri = base_uri
        self.db_path = db_path

    def __del__(self):
        """Clean up when garbage collected if not already closed.

        """
        self.close()

    def close(self):
        """Close any open resources in the database object.

        """
        pass

    def get_info(self):
        """Get version information about the database.

        This should return a dictionary with at least the following entries:

         - `backend`: the name of the backend used for this database.
         - `doccount`: the number of documents in the database.

        """
        raise NotImplementedError

    def get_schema(self):
        """Get the schema for the database.

        """
        raise NotImplementedError

    def get_document(self, db_path, doc_id):
        """Get a document from the database.

        Return the document data, as a dictionary keyed by fieldname, in which
        the values are lists of strings.

        If the document is not found, this should raise KeyError.

        """
        raise NotImplementedError

    def search_simple(self, query, start_index, end_index):
        """Perform a simple search, for a user-specified query string.

        Returns a set of search results.

        """
        raise NotImplementedError

    def search_similar(self, ids, start_index, end_index):
        """Perform a similarity search, for a list of ids.

        Returns a set of search results.

        """
        raise NotImplementedError


class BaseDbWriter(object):
    """Base class for databases returned by BaseBackend.get_db_writer().

    """
    def __init__(self, base_uri, db_path):
        """Create a database writer for the specified path.

        """
        self.base_uri = base_uri
        self.db_path = db_path

    def __del__(self):
        """Clean up when garbage collected if not already closed.

        """
        self.close()

    def close(self):
        """Close any open resources in the database object.

        """
        pass

    def set_schema(self, schema):
        """Set the schema for the database.

        """
        raise NotImplementedError

    def add_document(self, doc, docid=None):
        """Add a document to the database.

        """
        raise NotImplementedError

    def commit_changes(self):
        """Commit changes to the database.

        """
        raise NotImplementedError

