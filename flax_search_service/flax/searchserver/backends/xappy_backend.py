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
r"""Backend based on xappy.

"""
__docformat__ = "restructuredtext en"

# Local modules
from base_backend import BaseBackend, BaseDatabase
from flax.searchserver import schema, utils

# Global modules
import xapian
import xappy

# The metadata key used to hold schemas.
SCHEMA_KEY = "_flax_schema"

class Backend(BaseBackend):
    """The xappy backend for flax search server.

    """
    def version_info(self):
        """Get version information about the backend.

        """
        return 'xappy %s, xapian %s' % (
            xappy.__version__,
            xapian.version_string(),
        )

    def create_db(self, db_path):
        """Create a xappy database at db_path.

        """
        db = xappy.IndexerConnection(db_path)
        db.close()

    def delete_db(self, db_path):
        """Delete a xappy database at db_path.

        """
        pass

    def get_db(self, db_path, readonly):
        """Get the database at a specific path.

        """
        return Database(db_path, readonly)

class Database(BaseDatabase):
    def __init__(self, db_path, readonly):
        """Create a database object for the specified path.

        """
        BaseDatabase.__init__(self)
        self.db_path = db_path
        self.readonly = readonly
        self.conn = None

    def close(self):
        """Close any open database connections.

        """
        if self.conn is not None:
            self.conn.close()
            self.conn = None

    def _open_connection(self):
        """Open a search connection if there isn't one already open.

        """
        if self.conn is None:
            if self.readonly:
                self.conn = xappy.SearchConnection(self.db_path)
            else:
                self.conn = xappy.IndexerConnection(self.db_path)

    def get_info(self):
        """Get information about the database.

        """
        self._open_connection()
        return {
            'backend': 'xappy',
            'doccount': self.conn.get_doccount(),
        }

    def get_schema(self):
        """Get the schema for the database.

        """
        self._open_connection()
        data = self.conn.get_metadata(SCHEMA_KEY)
        if len(data) > 0:
            return schema.Schema(utils.json.loads(data))
        else:
            return schema.Schema()

    def set_schema(self, schema):
        """Get the schema for the database.

        """
        assert not self.readonly
        self._open_connection()
        self.conn.set_metadata(SCHEMA_KEY, utils.json.dumps(schema.as_dict()))
        schema.set_xappy_field_actions(self.conn)

    def get_document(self, doc_id):
        """Get a document from the database.

        """
        self._open_connection()
        return self.conn.get_document(doc_id).data

    def add_document(self, doc):
        """Add a document to the database.

        """
        assert not self.readonly
        self._open_connection()
        updoc = xappy.UnprocessedDocument()
        for k, v in doc.iteritems():
            if isinstance(v, list):
                for v2 in v:
                    updoc.append(k, v2)
            else:
                updoc.append(k, v)
        return self.conn.add(updoc)
