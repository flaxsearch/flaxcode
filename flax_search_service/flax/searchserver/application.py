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

# Global modules
import dircache
import os
import wsgiwapi
import xapian
import xappy

# Parameter descriptions
dbname_param = ('dbname', '^\w+$')
fieldname_param = ('fieldname', '^\w+$')

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
        dbpath = os.path.join(self.dbs_path, dbname)
        if not os.path.exists(dbpath):
            raise wsgiwapi.HTTPNotFound(request.path)
        return xappy.SearchConnection(dbpath)

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
        FIXME

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.noparams
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def schema_get_language(self, request):
        FIXME

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

    @wsgiwapi.allow_POST
    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def field_set(self, request):
        return 'field_set: %(dbname)s, %(fieldname)s' % request.pathinfo

    @wsgiwapi.allow_GETHEAD
    @wsgiwapi.pathinfo(dbname_param, fieldname_param)
    @wsgiwapi.jsonreturning
    def field_get(self, request):
        return 'field_get: %(dbname)s, %(fieldname)s' % request.pathinfo

    @wsgiwapi.allow_DELETE
    @wsgiwapi.pathinfo(dbname_param, fieldname_param)
    @wsgiwapi.jsonreturning
    def field_delete(self, request):
        return 'field_delete: %(dbname)s, %(fieldname)s' % request.pathinfo

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
            'dbs/*/schema/fields/*': wsgiwapi.MethodSwitch(
                get=self.field_get,
                post=self.field_set,
                delete=self.field_delete),
        }

def App(*args, **kwargs):
    server = SearchServer(*args, **kwargs)
    return wsgiwapi.make_application(server.get_urls())
