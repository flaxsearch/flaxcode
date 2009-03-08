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

# Parameter descriptions
dbname_param = ('dbname', '^\w+$')
fieldname_param = ('fieldname', '^\w+$')


@wsgiwapi.allow_GET
@wsgiwapi.noparams
@wsgiwapi.jsonreturning
def flax_status(request):
    return 'FlaxSearchServer version FIXME'

@wsgiwapi.pathinfo(dbname_param)
@wsgiwapi.jsonreturning
def db_info(request):
    return 'db_info: %s' % request.pathinfo['dbname']

@wsgiwapi.pathinfo(dbname_param)
@wsgiwapi.jsonreturning
def db_create(request):
    return 'db_create: %s' % request.pathinfo['dbname']

@wsgiwapi.pathinfo(dbname_param)
@wsgiwapi.jsonreturning
def db_delete(request):
    return 'db_delete: %s' % request.pathinfo['dbname']

@wsgiwapi.pathinfo(dbname_param)
@wsgiwapi.jsonreturning
def fields_info(request):
    return 'fields_info: %s' % request.pathinfo['dbname']

@wsgiwapi.pathinfo(dbname_param)
@wsgiwapi.jsonreturning
def field_set(request):
    return 'field_set: %(dbname)s, %(fieldname)s' % request.pathinfo

@wsgiwapi.pathinfo(dbname_param, fieldname_param)
@wsgiwapi.jsonreturning
def field_get(request):
    return 'field_get: %(dbname)s, %(fieldname)s' % request.pathinfo

@wsgiwapi.pathinfo(dbname_param, fieldname_param)
@wsgiwapi.jsonreturning
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
