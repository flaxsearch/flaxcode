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
import controller
import dbutils
import schema

# Global modules
import dircache
import os
import wsgiwapi
import xapian
import xappy

try:
    # json is a built-in module from python 2.6 onwards
    import json
    json.dumps
except (ImportError, AttributeError):
    import simplejson as json


# Parameter descriptions
dbname_param = ('dbname', '^[A-Za-z0-9._%]+$')
fieldname_param = ('fieldname', '^[A-Za-z0-9._%]+$')
docid_param = ('docid', '^[A-Za-z0-9._%]+$')

class SearchServer(object):
    """An instance of the search server.

    There will generally only be one of these per process.  An instance of the
    server will be wrapped in an WSGIWAPI application.

    """

    def __init__(self, settings):
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

        self.controller = controller.Controller(self.dbs_path,
                                                self.settings_db)

    def _get_search_connection(self, request):
        dbname = request.pathinfo['dbname']
        dbpath = dbutils.dbpath_from_urlquoted(self.dbs_path, dbname)
        if not os.path.exists(dbpath):
            raise wsgiwapi.HTTPNotFound(request.path)
        return xappy.SearchConnection(dbpath)

    def _get_indexer_connection(self, request):
        """ FIXME: this is just temporary. All DB writing should be moved into a 
        separate thread (one per DB), including config changes.
        """
        dbname = request.pathinfo['dbname']
        dbpath = dbutils.dbpath_from_urlquoted(self.dbs_path, dbname)
        if not os.path.exists(dbpath):
            raise wsgiwapi.HTTPNotFound(request.path)
        return xappy.IndexerConnection(dbpath)

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.noparams
    @wsgiwapi.jsonreturning
    def flax_status(self, request):
        """Get the status of the flax server.

        """
        import version
        return {
            'versions': {
                'SERVER': version.SERVER_VERSION,
                'PROTOCOL': version.PROTOCOL_VERSION,
                'xappy': xappy.__version__,
                'xapian': xapian.version_string(),
            }
        }

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.noparams
    @wsgiwapi.jsonreturning
    def dbnames(self, request):
        """Get a list of available databases.

        """
        if not os.path.isdir(self.dbs_path):
            names = []
        else:
            names = dircache.listdir(self.dbs_path)
        # FIXME - need to convert the filenames to dbnames, somehow.
        # (perhaps store DB name as metadata)?
        return names

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.noparams
    @wsgiwapi.jsonreturning
    def db_info(self, request):
        """Get information about the database.

        """
        conn = self._get_search_connection(request)
        return {
            'doccount': conn.get_doccount()
        }

    @wsgiwapi.allow_POST
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.param('overwrite', 1, 1, '^[01]$', [0],
                    "If 1, overwrite an existing database.  If 0 or omitted, "
                    "give an error if the database already exists.")
    @wsgiwapi.param('reopen', 1, 1, '^[01]$', [0],
                    "If 1, and database exists, do nothing.  If 0 or omitted, "
                    "give an error if the database already exists.")
    @wsgiwapi.jsonreturning
    def db_create(self, request):
        """Create a new database.

        """
        dbname = request.pathinfo['dbname']
        overwrite = bool(int(request.params['overwrite'][0]))
        reopen = bool(int(request.params['reopen'][0]))
        if overwrite and reopen:
            raise ValidationError('"overwrite" and "reopen" must not '
                                  'both be specified')
        self.controller.create_db(dbname, overwrite, reopen)
        dircache.reset()
        return True

    @wsgiwapi.allow_DELETE
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.param('allow_missing', 1, 1, '^[01]$', [0],
                    "If 1, and the database doesn't exist, do nothing.  If "
                    "0 or omitted, give an error if database doesn't exist.")
    @wsgiwapi.jsonreturning
    def db_delete(self, request):
        """Delete a database.

        """
        dbname = request.pathinfo['dbname']
        allow_missing = bool(int(request.params['allow_missing'][0]))
        self.controller.delete_db(dbname, allow_missing)
        dircache.reset()
        return True

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.noparams
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def schema_info(self, request):
        raise NotImplementedError

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.noparams
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def schema_get_language(self, request):
        raise NotImplementedError

    @wsgiwapi.allow_POST
    @wsgiwapi.param('language', 1, 1, '^\w+$', ['none'],
                    """The default language to use for this database.

                    Specify 'none' to do no language-specific processing.

                    Defaults to 'none'.
                    """)
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def schema_set_language(self, request):
        """Set
        """
        raise NotImplementedError

    @wsgiwapi.allow_POST
    @wsgiwapi.pathinfo(dbname_param, fieldname_param)
    @wsgiwapi.jsonreturning
    def field_set(self, request):
        con = self._get_indexer_connection(request)
        data = con.get_metadata('ss_schema')
        if data:
            scm = schema.Schema(json.loads(data))
            assert isinstance(scm, schema.Schema)  # FIXME
        else:
            scm = schema.Schema()
            
        scm.set_field(request.pathinfo['fieldname'], request.json)
        con.set_metadata('ss_schema', json.dumps(scm.as_dict()))
        con.flush()  # FIXME - move into write queue
        scm.set_xappy_field_actions(con)
        return True

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.pathinfo(dbname_param, fieldname_param)
    @wsgiwapi.jsonreturning
    def field_get(self, request):
        con = self._get_search_connection(request)
        data = con.get_metadata('ss_schema')
        if data:
            scm = schema.Schema(json.loads(data))
            assert isinstance(scm, schema.Schema)  # FIXME
            try:
                return scm.get_field(request.pathinfo['fieldname'])
            except KeyError:
                raise wsgiwapi.HTTPNotFound(request.path)
        else:
            return None

    @wsgiwapi.allow_DELETE
    @wsgiwapi.pathinfo(dbname_param, fieldname_param)
    @wsgiwapi.jsonreturning
    def field_delete(self, request):
        raise NotImplementedError

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def fields_list(self, request):
        con = self._get_search_connection(request)
        data = con.get_metadata('ss_schema')
        if data:
            scm = schema.Schema(json.loads(data))
            assert isinstance(scm, schema.Schema)  # FIXME
            return scm.get_field_names()
        else:
            return []

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.pathinfo(dbname_param, docid_param)
    @wsgiwapi.jsonreturning
    def doc_get(self, request):
        con = self._get_search_connection(request)
        doc = con.get_document(request.pathinfo['docid'])
        return doc.data

    @wsgiwapi.allow_POST
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def doc_add(self, request):
        """FIXME - move into write queue
        
        """
        con = self._get_indexer_connection(request)
        doc = xappy.UnprocessedDocument()
        assert isinstance(request.json, dict)
        for k, v in request.json.iteritems():
            if isinstance(v, list):
                for v2 in v:
                    doc.fields.append(xappy.Field(k, v2))
            else:
                doc.fields.append(xappy.Field(k, v))
        
        docid = con.add(doc)
        con.flush()
        return docid

    @wsgiwapi.allow_POST
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def doc_delete(self, request):
        raise NotImplementedError

    def get_urls(self):
        return {
            '': self.flax_status,
            'dbs': self.dbnames,
            'dbs/*': wsgiwapi.MethodSwitch(
                get=self.db_info,
                post=self.db_create,
                delete=self.db_delete),
            'dbs/*/schema': self.schema_info,
            'dbs/*/schema/language': wsgiwapi.MethodSwitch(
                get=self.schema_get_language,
                post=self.schema_set_language),
            'dbs/*/schema/fields': wsgiwapi.MethodSwitch(
                get=self.fields_list,),
            'dbs/*/schema/fields/*': wsgiwapi.MethodSwitch(
                get=self.field_get,
                post=self.field_set,
                delete=self.field_delete),
            'dbs/*/docs': wsgiwapi.MethodSwitch(
                post=self.doc_add),             
            'dbs/*/docs/*': wsgiwapi.MethodSwitch(
                get=self.doc_get,
                delete=self.doc_delete),
        }

def App(*args, **kwargs):
    server = SearchServer(*args, **kwargs)
    return wsgiwapi.make_application(server.get_urls(), logger=wsgiwapi.VerboseLogger)
