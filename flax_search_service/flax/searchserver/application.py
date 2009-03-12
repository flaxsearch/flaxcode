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

import wsgiwapi
import xappy
import xapian

# Parameter descriptions
dbname_param = ('dbname', '^\w+$')
fieldname_param = ('fieldname', '^\w+$')

class SearchServer(object):
    """An instance of the search server.

    There will generally only be one of these per process.  An instance of the
    server will be wrapped in an WSGIWAPI application.

    """

    def __init__(self, config):
        self.config = config

    @wsgiwapi.allow_GET
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

    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def db_info(self, request):
        dbname = request.pathinfo['dbname']
        return 'db_info: %s' % dbname

    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def db_create(self, request):
        return 'db_create: %s' % request.pathinfo['dbname']

    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def db_delete(self, request):
        return 'db_delete: %s' % request.pathinfo['dbname']

    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def fields_info(self, request):
        return 'fields_info: %s' % request.pathinfo['dbname']

    @wsgiwapi.pathinfo(dbname_param)
    @wsgiwapi.jsonreturning
    def field_set(self, request):
        return 'field_set: %(dbname)s, %(fieldname)s' % request.pathinfo

    @wsgiwapi.pathinfo(dbname_param, fieldname_param)
    @wsgiwapi.jsonreturning
    def field_get(self, request):
        return 'field_get: %(dbname)s, %(fieldname)s' % request.pathinfo

    @wsgiwapi.pathinfo(dbname_param, fieldname_param)
    @wsgiwapi.jsonreturning
    def field_delete(self, request):
        return 'field_delete: %(dbname)s, %(fieldname)s' % request.pathinfo

    def get_urls(self):
        return {
            '': self.flax_status,
            '*': {
                '': wsgiwapi.MethodSwitch(get=self.db_info,
                                          post=self.db_create,
                                          delete=self.db_delete),
                'fields': {
                    '': self.fields_info,
                    '*': wsgiwapi.MethodSwitch(get=self.field_get,
                                               post=self.field_set,
                                               delete=self.field_delete),
                },
            },
        }

def App(*args, **kwargs):
    server = SearchServer(*args, **kwargs)
    app = wsgiwapi.make_application(server.get_urls())
    return app()
