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

def build_query(conn, queryobj):
    """Build a xappy query from a connection and query object.

    """
    if queryobj is None:
        return conn.query_none()

    if queryobj.op == 'text':
        conn.query_parse(queryobj.search)
    else:
        raise wsgiwapi.HTTPError(400, "Invalid query type")

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

    def search_simple(self, query, start_rank, end_rank, default_op,
                      summary_fields, summary_maxlen, summary_hl):
        """Perform a simple search, for a user-specified query string.

        Returns a set of search results.

        """
        defop = self.searchconn.OP_AND
        if default_op == queries.Query.OR:
            defop = self.searchconn.OP_OR
        queryobj = self.searchconn.query_parse(query, default_op=defop)
        return self._search(queryobj, start_rank, end_rank, 
                            summary_fields, summary_maxlen, summary_hl)

    def search_similar(self, ids, pcutoff, start_rank, end_rank, 
                       summary_fields, summary_maxlen, summary_hl):
        """Perform a similarity search, for a user-specified query string.

        Returns a set of search results.

        """
        queryobj = self.searchconn.query_similar(ids, simterms=30)
        return self._search(queryobj, start_rank, end_rank, 
            summary_fields, summary_maxlen, summary_hl, pcutoff=pcutoff)

    def search_template(self, tmpl, params):
        if tmpl['content_type'] != 'text/javascript':
            raise ValueError('Template not in known language')
        tmpl = tmpl['template']
        import spidermonkey
        rt = spidermonkey.Runtime()
        cx = rt.new_context()

        class JsHttpError(object):
            def __init__(self, code, body):
                self.code = code
                self.body = body

        cx.add_global('params', params)
        cx.add_global('Query', queries.Query)
        cx.add_global('QueryText', queries.QueryText)
        cx.add_global('Search', queries.Search)
        cx.add_global('HttpError', JsHttpError)
        res = cx.execute(tmpl)

        if isinstance(res, JsHttpError):
            raise wsgiwapi.HTTPError(res.code, body=res.body)
        if not isinstance(res, Search):
            raise wsgiwapi.HTTPError(400, "Template didn't return a Search.")

        queryobj = build_query(self.searchconn, res.query)
        return self._search(queryobj, res.start_rank, res.end_rank, None, None, None,
                        pcutoff=res.percent_cutoff)

    def search_structured(self, query_all, query_any, query_none, query_phrase,
                          filters, start_rank, end_rank, summary_fields,
                          summary_maxlen, summary_hl):

        """Perform a structured search.

        FIXME: document

        """

        def combine_queries(q1, q2):
            if q1:
                return q1 & q2
            else:
                return q2

        query = None
        if query_all:
            query = self.searchconn.query_parse(query_all, default_op=self.searchconn.OP_AND)

        if query_any:
            query = combine_queries(query, self.searchconn.query_parse(
                query_any, default_op=self.searchconn.OP_OR))

        if query_none:
            if query is None:
                query = self.searchconn.query_all()
            query = query.and_not(self.searchconn.query_parse(query_none,
                                  default_op=self.searchconn.OP_OR))

        if query_phrase:   # FIXME - support in Xappy?
            raise NotImplementedError

        # we want filters to be ORd within fields, ANDed between fields
        if filters:
            filterdict = {}
            for f in filters:
                p = f.index(':')
                filterdict.setdefault(f[:p], []).append(
                    self.searchconn.query_field(f[:p], f[p+1:]))

            filterquery = self.searchconn.query_composite(self.searchconn.OP_AND,
                [self.searchconn.query_composite(self.searchconn.OP_OR, x)
                for x in filterdict.itervalues()])

            if query:
                query = query.filter(filterquery)
            else:
                query = filterquery

        return self._search(query, start_rank, end_rank, 
                            summary_fields, summary_maxlen, summary_hl)

    def _search(self, queryobj, start_rank, end_rank, 
                summary_fields, summary_maxlen, summary_hl, pcutoff=None):

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

        results = queryobj.search(start_rank, end_rank, percentcutoff=pcutoff)

        print '--', summary_fields, summary_maxlen, summary_hl

        def _summarise(result):
            data = {}
            for k, v in result.data.iteritems():
                if k in summary_fields:
                    data[k] = [result.summarise(k, summary_maxlen, summary_hl)]
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
