# Copyright (c) 2009 Tom Mortimer
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
r"""Define the web API bindings for FlaxSearchServer.

"""
__docformat__ = "restructuredtext en"

import wsgiwapi
#import database

def db_fn_deco(fn):
    """Multi-decorator for database functions.

    This specifies that we are returning JSON, and expecting the db name in the pathinfo.
    """
    @wsgiwapi.pathinfo(('dbname', '^\w+$', None),)
    @wsgiwapi.jsonreturning
    def fn2(r):
        return fn(r)
    return fn2

def field_fn_deco(fn):
    """Multi-decorator for field functions.
    
    The same as db_dn_deco, with the addition of the field name pathinfo.
    """
    @wsgiwapi.pathinfo(('dbname', '^\w+$', None),
                       ('fieldname', '^\w+$', None))
    @wsgiwapi.jsonreturning
    def fn2(r):
        return fn(r)
    return fn2

@wsgiwapi.allow_GET
@wsgiwapi.noparams
@wsgiwapi.jsonreturning
def flax_status(request):
    return 'FlaxSearchServer version FIXME'

@db_fn_deco
def db_info(request):
    return 'db_info: %s' % request.pathinfo['dbname']

@db_fn_deco
def db_create(request):
    return 'db_create: %s' % request.pathinfo['dbname']

@db_fn_deco
def db_delete(request):
    return 'db_delete: %s' % request.pathinfo['dbname']

@db_fn_deco
def fields_info(request):
    return 'fields_info: %s' % request.pathinfo['dbname']

@db_fn_deco
def field_set(request):
    return 'field_set: %(dbname)s, %(fieldname)s' % request.pathinfo

@field_fn_deco
def field_get(request):
    return 'field_get: %(dbname)s, %(fieldname)s' % request.pathinfo

@field_fn_deco
def field_delete(request):
    return 'field_delete: %(dbname)s, %(fieldname)s' % request.pathinfo


app = wsgiwapi.make_application({
    '': flax_status,
    '*': { 
        '': wsgiwapi.MethodSwitch(get=db_info, post=db_create, delete=db_delete),
        'fields': { 
            '': fields_info,
            '*': wsgiwapi.MethodSwitch(get=field_get, post=field_set, delete=field_delete),
        },
    },
})

server = wsgiwapi.make_server(app(), ('0.0.0.0', 8080))
try:
    server.start()
except KeyboardInterrupt:
    server.stop()
 
 