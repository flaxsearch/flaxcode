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
r"""WSGI application for FlaxSearchServer.

"""
__docformat__ = "restructuredtext en"

# Local modules
import backends
import controller
import queries
import schema
import utils

# Global modules
import os
from wsgiwapi import Resource, ValidationError, pathinfo, param, noparams, \
    jsonreturning, \
    allow_GETHEAD, allow_POST, allow_PUT, allow_DELETE, \
    HTTPError, HTTPNotFound, make_application, VerboseLogger
import xapian

# Parameter descriptions
dbname_param = ('dbname', '^[A-Za-z0-9._%]+$')
fieldname_param = ('fieldname', '^[A-Za-z0-9._%]+$')
tmplname_param = ('tmplname', '^[A-Za-z0-9._%]+$')
docid_param = ('docid', '^[A-Za-z0-9._%]+$')
metakey_param = ('metakey', '^[A-Za-z0-9._%]+$')


class DbResource(Resource):
    """Create, delete and get information about a database.

    """
    def __init__(self, controller):
        Resource.__init__(self)
        self.controller = controller


    @pathinfo(dbname_param)
    @noparams
    @jsonreturning
    def get(self, request):
        """Get information about the database.

        """
        dbname = request.pathinfo['dbname']
        db = self.controller.get_db_reader(dbname)
        return db.get_info()


    @pathinfo(dbname_param)
    @param('overwrite', 1, 1, '^[01]$', [0],
           "If 1, overwrite an existing database.  If 0 or omitted, "
           "give an error if the database already exists.")
    @param('reopen', 1, 1, '^[01]$', [0],
           "If 1, and database exists, do nothing.  If 0 or omitted, "
           "give an error if the database already exists.")
    @param('backend', 1, 1, '^[a-z][a-z0-9]*$', ['xappy'],
           "The database backend to use. Defaults to xappy.")
    @jsonreturning
    def post(self, request):
        """Create a new database.

        """
        dbname = request.pathinfo['dbname']
        overwrite = bool(int(request.params['overwrite'][0]))
        reopen = bool(int(request.params['reopen'][0]))
        if overwrite and reopen:
            raise ValidationError('"overwrite" and "reopen" must not '
                                           'both be specified')
        self.controller.create_db(request.params['backend'][0],
                                  dbname, overwrite, reopen)
        return True

    @pathinfo(dbname_param)
    @param('allow_missing', 1, 1, '^[01]$', [0],
                    "If 1, and the database doesn't exist, do nothing.  If "
                    "0 or omitted, give an error if database doesn't exist.")
    @jsonreturning
    def delete(self, request):
        """Delete a database.

        """
        dbname = request.pathinfo['dbname']
        allow_missing = bool(int(request.params['allow_missing'][0]))
        self.controller.delete_db(dbname, allow_missing)
        return True


class SearchServer(object):
    """An instance of the search server.

    There will generally only be one of these per process.  An instance of the
    server will be wrapped in an WSGIWAPI application.

    """

    def __init__(self, settings):
        """Initialise an instance of the search server.

        `settings` should be a dictionary containing the following items:

         - `data_path`: The path of a directory under which all the databases
           and other data will be placed.
         - `server_bind_address`: The address for the server to bind to.  This
           should by a tuple containing two items - first the address to bind
           to (for example, '0.0.0.0' to bind to any IPv4 address), second
           the port number to bind to.

        `settings` may also contain the following optional items:

         - `backend_settings`: A dictionary of backend-specific settings, keyed
           by backend name.  These will be passed directly to the backend in
           use.

        For example:

        >>> s = SearchServer({'data_path': '/tmp/flax/',
        ...                   'server_bind_address': ('0.0.0.0', 8080),
        ...                  })

        The directory pointed to by data_path will be created if it doesn't
        already exist.

        """
        self.data_path = os.path.realpath(settings['data_path'])
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

        self.dbs_path = os.path.join(self.data_path, 'ss_dbs')
        if not os.path.exists(self.dbs_path):
            os.makedirs(self.dbs_path)

        # Open a writer on the settings database, which ensures that only one
        # search server is running at a time.  Also used to hold settings which
        # are set at runtime.
        self.settings_path = os.path.join(self.data_path, 'ss_settings')
        self.settings_db = xapian.WritableDatabase(self.settings_path,
                                                   xapian.DB_CREATE_OR_OPEN)

        self.backend_settings = settings.get('backend_settings', {})
        backends.check_backend_settings(self.backend_settings)

        self.controller = controller.Controller(settings['base_uri'],
                                                self.dbs_path,
                                                self.backend_settings,
                                                self.settings_db,
                                               )

    @allow_GETHEAD
    @noparams
    @jsonreturning
    def flax_status(self, request):
        """Get the status of the flax server.

        """
        import version
        backend_list = backends.get_backends()
        backend_versions = dict((name, backend.version_info())
                                for name, backend in backend_list)
        return {
            'versions': {
                'SERVER': version.SERVER_VERSION,
                'PROTOCOL': version.PROTOCOL_VERSION,
            },
            'backends': backend_versions,
        }

    #### DB methods ####

    @allow_GETHEAD
    @noparams
    @jsonreturning
    def dbnames(self, request):
        """Get a list of available databases.

        """
        return self.controller.db_names()


    @allow_POST
    @pathinfo(dbname_param)
    @jsonreturning
    def db_flush(self, request):
        """Flush changes to the database.

        FIXME: this is a hack!
        (we also need to support automatic flushing).
        """
        dbname = request.pathinfo['dbname']
        self.controller.flush(dbname)
        return True

    #### schema methods ####

    @allow_GETHEAD
    @noparams
    @pathinfo(dbname_param)
    @jsonreturning
    def schema_info(self, request):
        dbname = request.pathinfo['dbname']
        db = self.controller.get_db_reader(dbname)
        scm = db.get_schema()
        return scm.as_dict()

    @allow_GETHEAD
    @noparams
    @pathinfo(dbname_param)
    @jsonreturning
    def schema_get_language(self, request):
        dbname = request.pathinfo['dbname']
        db = self.controller.get_db_reader(dbname)
        scm = db.get_schema()
        return scm.language

    @allow_POST
    @param('language', 1, 1, '^\w+$', ['none'],
           """The default language to use for this database.

           Specify 'none' to do no language-specific processing.

           Defaults to 'none'.
           """)
    @pathinfo(dbname_param)
    @jsonreturning
    def schema_set_language(self, request):
        """Set the default language for language for the database.

        """
        dbname = request.pathinfo['dbname']
        language = request.pathinfo['language']

        dbr = self.controller.get_db_reader(dbname)
        dbw = self.controller.get_db_writer(dbname)
        scm = dbr.get_schema()
        scm.language = language
        dbw.set_schema(scm)
        # FIXME - should we flush this immediately?

        return True

    #### schema/field methods ####

    @allow_POST
    @allow_PUT
    @pathinfo(dbname_param, fieldname_param)
    @jsonreturning
    def field_set(self, request):
        """Set the configuration for a field.

        """
        dbname = request.pathinfo['dbname']
        fieldname = request.pathinfo['fieldname']
        dbr = self.controller.get_db_reader(dbname)
        scm = dbr.get_schema()

#        # don't overwrite existing field
#        if request.method == 'POST' and fieldname in scm.get_field_names():
#            return JsonResponse(False, 409)

        try:
            scm.set_field(fieldname, request.json)
            dbw = self.controller.get_db_writer(dbname)
            dbw.set_schema(scm)
            self.controller.flush(dbname)
            return True
        except schema.FieldError, e:
            raise HTTPError(400, e.message)

    @allow_GETHEAD
    @pathinfo(dbname_param, fieldname_param)
    @jsonreturning
    def field_get(self, request):
        dbname = request.pathinfo['dbname']
        fieldname = request.pathinfo['fieldname']

        db = self.controller.get_db_reader(dbname)
        scm = db.get_schema()
        try:
            return scm.get_field(fieldname)
        except KeyError:
            raise HTTPNotFound()

    @allow_DELETE
    @pathinfo(dbname_param, fieldname_param)
    @jsonreturning
    def field_delete(self, request):
        dbname = request.pathinfo['dbname']
        fieldname = request.pathinfo['fieldname']

        dbr = self.controller.get_db_reader(dbname)
        scm = dbr.get_schema()
        try:
            scm.get_field(fieldname) # check it exists
        except KeyError:
            raise HTTPNotFound()

        scm.delete_field(fieldname)
        dbw = self.controller.get_db_writer(dbname)
        dbw.set_schema(scm)
        self.controller.flush(dbname)
        return True

    @allow_GETHEAD
    @pathinfo(dbname_param)
    @jsonreturning
    def fields_list(self, request):
        dbname = request.pathinfo['dbname']
        db = self.controller.get_db_reader(dbname)
        scm = db.get_schema()
        return scm.get_field_names()

    @allow_GETHEAD
    @pathinfo(dbname_param, tmplname_param)
    @jsonreturning
    def template_get(self, request):
        """Get a template.

        """
        dbname = request.pathinfo['dbname']
        tmplname = request.pathinfo['tmplname']

        dbr = self.controller.get_db_reader(dbname)
        scm = dbr.get_schema()
        try:
            return scm.get_template(tmplname)
        except KeyError:
            raise HTTPNotFound()

    @allow_POST
    @allow_PUT
    @pathinfo(dbname_param, tmplname_param)
    @jsonreturning
    def template_set(self, request):
        """Set a template.

        """
        dbname = request.pathinfo['dbname']
        tmplname = request.pathinfo['tmplname']
        dbr = self.controller.get_db_reader(dbname)
        scm = dbr.get_schema()

#        # don't overwrite existing template
#        if request.method == 'POST' and tmplname in scm.get_template_names():
#            return JsonResponse(False, 409)

        try:
            scm.set_template(tmplname, request.raw_post_data, request.content_type)
            dbw = self.controller.get_db_writer(dbname)
            dbw.set_schema(scm)
            self.controller.flush(dbname)
            return True
        except schema.FieldError, e:
            raise HTTPError(400, e.message)

    #### document methods ####

    @allow_GETHEAD
    @pathinfo(dbname_param, docid_param)
    @jsonreturning
    def doc_get(self, request):
        dbname = request.pathinfo['dbname']
        doc_id = request.pathinfo['docid']
        db = self.controller.get_db_reader(dbname)
        try:
            return db.get_document(doc_id)
        except KeyError:
            raise HTTPNotFound()

    @allow_POST
    @pathinfo(dbname_param)
    @jsonreturning
    def doc_add(self, request):
        """Add document.

        NOTE: strictly speaking, creating a resource should return status 201
        with the resource location in the Location: header. However, this
        causes the PHP HTTP client to redirect, which is not what we want! So
        we'll bend the REST rules and always return 200 for success, with the
        docid (or whatever) in the body.

        NOTE: currently not returning doc ID, since we can't get it from Xappy
        until the doc is (asynchronously) added. A possible solution is to
        set a UUID or similar.
        """
        assert isinstance(request.json, dict)
        dbname = request.pathinfo['dbname']
        dbw = self.controller.get_db_writer(dbname)
        dbw.add_document(request.json)
        return True

    @allow_POST
    @pathinfo(dbname_param, docid_param)
    @jsonreturning
    def doc_add2(self, request):
        """Add or replace a document with a specfied ID.

        """
        assert isinstance(request.json, dict)
        dbname = request.pathinfo['dbname']
        dbw = self.controller.get_db_writer(dbname)
        dbw.add_document(request.json, docid=request.pathinfo['docid'])
        return True

    @allow_DELETE
    @pathinfo(dbname_param, docid_param)
    @jsonreturning
    def doc_delete(self, request):
        dbname = request.pathinfo['dbname']
        dbw = self.controller.get_db_writer(dbname)
        dbw.delete_document(request.pathinfo['docid'])
        return True

    #### Search methods ####

    # Define our common decorators once, it saves space and conforms to DRY.
    # But unlike folding them into a super-decorator, it won't break WSGIWAPI /doc

    _start_rank_decor = param('start_rank', 0, 1, '^\d*$', ['0'],
        """The offset of the first document to return.

        0-based - ie, 0 returns the top document first.

        """)
    _end_rank_decor = param('end_rank', 0, 1, '^\d+$', ['10'],
        """The rank one past the last hit to return.

        e.g. the defaults return the 10 hits ranked 0-9.
        Note that the search may return fewer hits than requested.
        """)
    _default_op_decor = param('default_op', 0, 1, '^OR|AND$', ['AND'],
        """The default operator to use for free-text queries.

        Defaults to AND (ie, all the words are required).
        """)
    _summary_field_decor = param('summary_field', 0, None, '^[A-Za-z0-9._%]+$', [],
        """Field to summarise in returned docs.

        This replaces the whole field returned with just the summary,
        optionally highlighted.

        """)
    _summary_maxlen_decor = param('summary_maxlen', 0, 1, '^\d+$', ['500'],
        """The maximum length for the summary in any single field instance.

        """)
    _highlight_bra_decor = param('highlight_bra', 0, 1, None, [''],
        """String to insert before a highlighted word in a summary.

        """)
    _highlight_ket_decor = param('highlight_ket', 0, 1, None, [''],
        """String to insert after a highlighted word in a summary.

        """)

    @allow_GETHEAD
    @pathinfo(dbname_param)
    @jsonreturning
    @_start_rank_decor
    @_end_rank_decor
    @_default_op_decor
    @_summary_field_decor
    @_summary_maxlen_decor
    @_highlight_bra_decor
    @_highlight_ket_decor
    @param('query', 0, None, None, [''],
           """A user-entered query string.

           """)
    def search_simple(self, request):
        """Perform a search using a simple user-entered query.

        """
        dbname = request.pathinfo['dbname']
        start_rank = int(request.params['start_rank'][0])
        end_rank = int(request.params['end_rank'][0])
        default_op = {'AND': queries.Query.AND,
            'OR': queries.Query.OR}[request.params['default_op'][0]]
        summary_fields = set(request.params['summary_field'])
        summary_maxlen = int(request.params['summary_maxlen'][0])
        summary_hl = (request.params['highlight_bra'][0], request.params['highlight_ket'][0])
        db = self.controller.get_db_reader(dbname)

        qlist = [queries.QueryText(querystr.decode('utf-8'), default_op=default_op)
                 for querystr in request.params['query']]
        search = queries.Search(queries.Query.compose(queries.Query.OR, qlist),
                                start_rank, end_rank,
                                summary_fields=summary_fields,
                                summary_maxlen=summary_maxlen,
                                summary_hl=summary_hl)
        return db.search(search)

    @allow_GETHEAD
    @pathinfo(dbname_param, tmplname_param)
    @jsonreturning
    def search_template(self, request):
        """Perform a search using the template named in the URI.

        """
        dbname = request.pathinfo['dbname']
        tmplname = request.pathinfo['tmplname']
        db = self.controller.get_db_reader(dbname)
        scm = db.get_schema()
        tmpl = scm.get_template(tmplname)
        if tmpl['content_type'] != 'text/javascript':
            raise ValueError('Template not in known language')
        tmpl = tmpl['template']
        import jstemplates
        env = jstemplates.JsTemplateEvaluator()
        search = env.search_template(tmpl, request.params)
        return db.search(search)

    @allow_GETHEAD
    @pathinfo(dbname_param)
    @jsonreturning
    @param('query', 0, None, None, [''],
           """A user-entered query string.

           """)
    def search_spell(self, request):
        """Look for spelling corrections for the query string.

        """
        dbname = request.pathinfo['dbname']
        db = self.controller.get_db_reader(dbname)
        return [db.spell_correct(query) for query in request.params['query']]

    @allow_GETHEAD
    @pathinfo(dbname_param)
    @jsonreturning
    @_start_rank_decor
    @_end_rank_decor
    @_summary_field_decor
    @_summary_maxlen_decor
    @_highlight_bra_decor
    @_highlight_ket_decor
    @param('id', 1, None, None, None,
           """The ids to use for the similarity search.

           """)
    @param('pcutoff', 0, 1, '^\d+$', ['0'],
           """Percentage cutoff.

           Only return hits with a percentage weight above this value.
           """)
    def search_similar(self, request):
        """Perform a similarity search for one or more items.

        """
        dbname = request.pathinfo['dbname']
        ids = request.params['id']
        start_rank = int(request.params['start_rank'][0])
        end_rank = int(request.params['end_rank'][0])
        summary_fields = set(request.params['summary_field'])
        summary_maxlen = int(request.params['summary_maxlen'][0])
        summary_hl = (request.params['highlight_bra'][0], request.params['highlight_ket'][0])
        pcutoff = int(request.params['pcutoff'][0])
        db = self.controller.get_db_reader(dbname)

        search = queries.Search(queries.QuerySimilar(ids),
                                start_rank, end_rank,
                                percent_cutoff=pcutoff,
                                summary_fields=summary_fields,
                                summary_maxlen=summary_maxlen,
                                summary_hl=summary_hl)
        return db.search(search)

    @allow_GETHEAD
    @pathinfo(dbname_param)
    @jsonreturning
    @_start_rank_decor
    @_end_rank_decor
    @_summary_field_decor
    @_summary_maxlen_decor
    @_highlight_bra_decor
    @_highlight_ket_decor
    @param('query_all', 0, 1, None, [''],
           """A user-entered query string matching all terms.

           """)
    @param('query_any', 0, 1, None, [''],
           """A user-entered query string matching any terms.

           """)
    @param('query_none', 0, 1, None, [''],
           """A user-entered query string matching no terms.

           """)
    @param('query_phrase', 0, 1, None, [''],
           """A user-entered query string matching a phrase.

           """)
    @param('filter', 0, None, None, [],
           """A filter on a specified field.

           Format: fieldname:query text
           """)
    def search_structured(self, request):
        """Search a structured query.

        """
        dbname = request.pathinfo['dbname']
        db = self.controller.get_db_reader(dbname)
        summary_fields = set(request.params['summary_field'])
        summary_maxlen = int(request.params['summary_maxlen'][0])
        summary_hl = (request.params['highlight_bra'][0], request.params['highlight_ket'][0])

        query_all = request.params['query_all'][0].decode('utf-8')
        query_any = request.params['query_any'][0].decode('utf-8')
        query_none = request.params['query_none'][0].decode('utf-8')
        query_phrase = request.params['query_phrase'][0].decode('utf-8')
        filters = [p.decode('utf-8') for p in request.params['filter']]

        queryobj = None
        if query_all:
            # A query in which all terms must be present
            queryobj = queries.QueryText(query_all,
                                         default_op=queries.Query.AND)

        if query_any:
            # A query in which at least one term must be present
            queryobj2 = queries.QueryText(query_any,
                                          default_op=queries.Query.OR)
            if queryobj is None:
                queryobj = queryobj2
            else:
                queryobj = queryobj & queryobj2

        if query_none:
            # A query in which none of the terms may be present
            if queryobj is None:
                queryobj = queries.QueryAll()
            queryobj = queryobj - queries.QueryText(query_none,
                                            default_op=queries.Query.OR)

        if query_phrase:
            raise NotImplementedError

        if filters:
            filterdict = {}
            for f in filters:
                p = f.index(u':')
                filterdict.setdefault(f[:p], []).append(
                    queries.QueryExact(f[p+1:], f[:p]))

            filterquery = queries.QueryAnd(
                [queries.QueryOr(x) for x in filterdict.itervalues()])

            if queryobj is None:
                queryobj = filterquery
            else:
                queryobj = queryobj.filter(filterquery)

        search = queries.Search(queryobj,
                                int(request.params['start_rank'][0]),
                                int(request.params['end_rank'][0]),
                                summary_fields=summary_fields,
                                summary_maxlen=summary_maxlen,
                                summary_hl=summary_hl)
        print repr(search)
        return db.search(search)

    #### term methods (HACK) ####

    @allow_GETHEAD
    @pathinfo(dbname_param, fieldname_param)
    @jsonreturning
    @param('starts_with', 0, 1, None, [''],
                    """Only return terms starting with this string.

                    """)
    @param('max_terms', 0, 1, '^\d+$', ['100'],
                    """Maximum number of terms to return

                    """)
    def get_terms(self, request):
        dbname = request.pathinfo['dbname']
        fieldname = request.pathinfo['fieldname']
        db = self.controller.get_db_reader(dbname)
        return db.get_terms(fieldname, request.params['starts_with'][0],
                            int(request.params['max_terms'][0]))

    #### metadata methods ####
    
    @allow_GETHEAD
    @pathinfo(dbname_param, metakey_param)
    @jsonreturning
    def metadata_get(self, request):    
        dbname = request.pathinfo['dbname']
        metakey = request.pathinfo['metakey']

        db = self.controller.get_db_reader(dbname)
        try:
            return db.get_metadata(metakey)
        except KeyError:
            raise HTTPNotFound()

    @allow_POST
    @allow_PUT
    @pathinfo(dbname_param, metakey_param)
    @jsonreturning
    def metadata_set(self, request):    
        dbname = request.pathinfo['dbname']
        metakey = request.pathinfo['metakey']

        db = self.controller.get_db_writer(dbname)
        db.set_metadata(metakey, request.json)
        return 1
        
    #### end of implementations ####

    def get_urls(self):
        return {
            '': self.flax_status,
            'v1/dbs': self.dbnames,
            'v1/dbs/*': DbResource(self.controller),
            'v1/dbs/*/flush': self.db_flush,
            'v1/dbs/*/schema': self.schema_info,
            'v1/dbs/*/schema/language': Resource(
                get=self.schema_get_language,
                post=self.schema_set_language),
            'v1/dbs/*/schema/fields': Resource(
                get=self.fields_list,),
            'v1/dbs/*/schema/fields/*': Resource(
                get=self.field_get,
                post=self.field_set,
                put=self.field_set,
                delete=self.field_delete),
            'v1/dbs/*/schema/templates/*': Resource(
                get=self.template_get,
                post=self.template_set,
                put=self.template_set),
            'v1/dbs/*/docs': Resource(
                post=self.doc_add),
            'v1/dbs/*/docs/*': Resource(
                get=self.doc_get,
                post=self.doc_add2,
                put=self.doc_add2,
                delete=self.doc_delete),
            'v1/dbs/*/search/simple': self.search_simple,
            'v1/dbs/*/search/spell': self.search_spell,
            'v1/dbs/*/search/similar': self.search_similar,
            'v1/dbs/*/search/structured': self.search_structured,
            'v1/dbs/*/search/template/*': self.search_template,
            'v1/dbs/*/terms/*': self.get_terms,
            'v1/dbs/*/meta/*': Resource(
                get=self.metadata_get,
                post=self.metadata_set,
                put=self.metadata_set),
        }

def App(*args, **kwargs):
    server = SearchServer(*args, **kwargs)
    return make_application(server.get_urls(), logger=VerboseLogger, autodoc='doc')
