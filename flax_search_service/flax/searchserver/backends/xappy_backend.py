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
from base_backend import BaseBackend, BaseDbReader, BaseDbWriter
from flax.searchserver import schema, utils, queries

# Global modules
import Queue
import wsgiwapi
import xapian
import xappy

# The metadata key used to hold schemas.
SCHEMA_KEY = "_flax_schema"

op_convert = {
    queries.Query.AND: xappy.SearchConnection.OP_AND,
    queries.Query.OR: xappy.SearchConnection.OP_OR,
}

def build_query(conn, query):
    """Build a xappy query from a connection and a Query object.

    """
    if query is None or query.op is None:
        return conn.query_none()

    if isinstance(query, queries.QueryCombination):
        if len(query.subqs) == 0:
            return conn.query_none()
        subqs = [build_query(conn, subq) for subq in query.subqs]

        if isinstance(query, queries.QueryOr):
            return conn.query_composite(conn.OP_OR, subqs)

        elif isinstance(query, queries.QueryAnd):
            return conn.query_composite(conn.OP_AND, subqs)

        elif isinstance(query, queries.QueryXor):
            res = subqs[0]
            for subq in subqs[1]:
                res = res ^ subq
            return res

        elif isinstance(query, queries.QueryNot):
            lhs = subqs[0]
            rhs = conn.query_composite(conn.OP_OR, subqs[1:])
            return lhs.and_not(rhs)

        raise wsgiwapi.HTTPError(400, "Invalid combination query type (%r)" % query.op)

    elif isinstance(query, queries.QueryMultWeight):
        return build_query(conn, query.subq) * query.mult

    elif isinstance(query, queries.QueryText):
        defop = op_convert.get(query.default_op)
        if defop is None:
            raise wsgiwapi.HTTPError(400, "Invalid operator specified for "
                                     "default operator for text query.")

        if query.fields is not None:
            raise wsgiwapi.HTTPError(400, "Searching within specific fields not yet implemented")

        return conn.query_parse(query.text,
                                allow=query.fields,
                                default_op=defop)

    elif isinstance(query, queries.QueryExact):
        # FIXME - this only works correctly if all the fields supplied have
        # been marked as index-as-exact: but this isn't checked.
        return conn.query_composite(conn.OP_AND,
                                    [conn.query_field(field, query.text)
                                    for field in query.fields])

    elif isinstance(query, queries.QuerySimilar):
        return conn.query_similar(query.ids, simterms=query.simterms)

    else:
        raise wsgiwapi.HTTPError(400, "Invalid query type (%r)" % query.op)

class Backend(BaseBackend):
    """The xappy backend for flax search server.

    Settings for this backend can be specified in the settings.py module by
    adding a 'xappy' entry to the 'backend_settings' dict.  They will be
    available in self.settings.

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

    def get_db_reader(self, base_uri, db_path):
        """Get a DbReader object for a database at a specific path.

        We allow multiple DbReaders so that searches can be concurrent.

        """
        return DbReader(base_uri, db_path)

    def get_db_writer(self, base_uri, db_path):
        """Get a DbWriter object for a database at a specific path.

        There should only be one of these in existence at any one time (per DB).

        """
        return DbWriter(base_uri, db_path)

class DbReader(BaseDbReader):
    """A reader obtined by Backend.get_db_reader().

    """
    def __init__(self, base_uri, db_path):
        """Create a database reader for the specified path.

        """
        BaseDbReader.__init__(self, base_uri, db_path)
        self._sconn = None

    @property
    def searchconn(self):
        """Open a search connection if there isn't one already open.

        """
        if self._sconn is None:
            self._sconn = xappy.SearchConnection(self.db_path)
        return self._sconn

    def close(self):
        """Close any open resources in the database object.

        """
        if self._sconn is not None:
            self._sconn.close()
            self._sconn = None

    def get_info(self):
        """Get information about the database.

        """
        return {
            'backend': 'xappy',
            'doccount': self.searchconn.get_doccount(),
        }

    def get_schema(self):
        """Get the schema for the database.

        """
        data = self.searchconn.get_metadata(SCHEMA_KEY)
        if len(data) > 0:
            return schema.Schema(utils.json.loads(data))
        else:
            return schema.Schema()

    def get_document(self, doc_id):
        """Get a document from the database.

        """
        return self.searchconn.get_document(doc_id).data

    def search(self, search):
        """Perform a search, as described by a Search object.

        Returns a dictionary of properties giving information about the search
        results.

        """
        queryobj = build_query(self.searchconn, search.query)
        if queryobj is None:
            return {
                'matches_estimated': 0,
                'matches_lower_bound': 0,
                'matches_upper_bound': 0,
                'matches_human_readable_estimate': '',
                'estimate_is_exact': True,
                'more_matches': False,
                'start_rank': 0,
                'end_rank': 0,
                'results': [],
            }

        results = queryobj.search(search.start_rank, search.end_rank,
                                  None, None, None,
                                  percentcutoff=search.percent_cutoff)

        def _summarise(result):
            if search.summary_fields is None:
                return result.data
            data = {}
            for k, v in result.data.iteritems():
                if k in search.summary_fields:
                    data[k] = [result.summarise(k, search.summary_maxlen, search.summary_hl)]
                else:
                    data[k] = v
            return data

        resultlist = [
            {
                "docid": result.id,
                "rank": result.rank,
                "db": self.base_uri,
                "weight": result.weight,
                "data": _summarise(result),
            } for result in results
        ]

        return {
            'matches_estimated': results.matches_estimated,
            'matches_lower_bound': results.matches_lower_bound,
            'matches_upper_bound': results.matches_upper_bound,
            'matches_human_readable_estimate': results.matches_human_readable_estimate,
            'estimate_is_exact': results.estimate_is_exact,
            'more_matches': results.more_matches,
            'start_rank': results.startrank,
            'end_rank': results.endrank,
            'results': resultlist,
        }

    def spell_correct(self, query):
        return self.searchconn.spell_correct(query)

    def get_terms(self, fieldname, starts_with, max_terms):
        """Return list of terms (without prefix) for the specified fieldname.
        
        `starts_with`: returned terms must start with this string.
        `max_terms`: maximum number of terms to return.
        
        """
        it = self.searchconn.iter_terms_for_field(fieldname, starts_with)
        ret = []
        for term in it:
            ret.append(term)
            if len(ret) == max_terms:
                break
        
        return ret

class DbWriter(BaseDbWriter):
    """A reader obtined by Backend.get_db_reader().

    """
    def __init__(self, base_uri, db_path):
        """Create a database writer for the specified path.

        """
        BaseDbWriter.__init__(self, base_uri, db_path)
        self.queue = Queue.Queue(1000)
        if not hasattr(self.queue, 'task_done'):
            def nop(*args): pass
            self.queue.task_done = nop
        if not hasattr(self.queue, 'join'):
            def nop(*args): pass
            self.queue.join = nop
        self.iconn = xappy.IndexerConnection(self.db_path)

    def close(self):
        """Close any open database connections.

        """
        self.iconn.close()

    def set_schema(self, schema):
        """Set the schema for this database.

        This will be done asynchronously in the write thread.

        """
        self.queue.put(DbWriter.SetSchemaAction(self, schema))

    def add_document(self, doc, docid=None):
        """Add a document to the database.

        This will be done asynchronously in the write thread.

        """
        self.queue.put(DbWriter.AddDocumentAction(self, doc, docid))

    def delete_document(self, docid):
        """Delete a document from the database.

        This will be done asynchronously in the write thread.

        """
        self.queue.put(DbWriter.DeleteDocumentAction(self, docid))

    def commit_changes(self):
         """Commit changes to the database.

         This will be done asynchronously in the write thread.

         """
         self.queue.put(DbWriter.CommitAction(self))


    class SetSchemaAction(object):
        """Action to set the schema for a Xappy database.

        """
        def __init__(self, db_writer, schema):
            self.db_writer = db_writer
            self.schema = schema

        def perform(self):
            self.db_writer.iconn.set_metadata(SCHEMA_KEY, utils.json.dumps(self.schema.as_dict()))
            self.schema.set_xappy_field_actions(self.db_writer.iconn)

        def __str__(self):
            return 'SetSchemaAction(%s)' % self.db_writer.db_path


    class AddDocumentAction(object):
        """Action to add a document to a Xappy database.

        """
        def __init__(self, db_writer, doc, docid=None):
            self.db_writer = db_writer
            self.doc = doc
            self.docid = docid

        def perform(self):
            updoc = xappy.UnprocessedDocument()
            for k, v in self.doc.iteritems():
                if isinstance(v, list):
                    for v2 in v:
                        updoc.append(k, v2)
                else:
                    updoc.append(k, v)

            if self.docid is not None:
                updoc.id = self.docid
                self.db_writer.iconn.replace(updoc)
            else:
                self.db_writer.iconn.add(updoc)

        def __str__(self):
            return 'AddDocumentAction(%s)' % self.db_writer.db_path

    class DeleteDocumentAction(object):
        """Action to delete a document from a Xappy database.

        """
        def __init__(self, db_writer, docid):
            self.db_writer = db_writer
            self.docid = docid

        def perform(self):
            self.db_writer.iconn.delete(self.docid)

        def __str__(self):
            return 'DeleteDocumentAction(%s)' % self.db_writer.db_path

    class CommitAction(object):
        """Action to flush changes to the database so they can be searched.

        """
        def __init__(self, db_writer):
            self.db_writer = db_writer

        def perform(self):
            self.db_writer.iconn.flush()

        def __str__(self):
            return 'CommitAction(%s)' % self.db_writer.db_path
