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
r"""Evaluation of javascript templates.

"""
__docformat__ = "restructuredtext en"

# Global modules
import wsgiwapi
import spidermonkey
import queries

class JsHttpError(object):
    """Class used for reporting Http errors from javascript.

    """
    def __init__(self, code, body):
        self.code = code
        self.body = body

import traceback
def access_checker(obj, name):
    try:
        if isinstance(name, int):
            return True
        return not name.startswith('_') or name in ('__call__',)
    except:
        # Don't pass error to javascript.
        # FIXME - should log this somewhere.
        return False

class JsTemplateEvaluator(object):
    def __init__(self):
        self._rt = None

    @property
    def rt(self):
        if self._rt is None:
            self._rt = spidermonkey.Runtime()
        return self._rt

    def search_template(self, tmpl, params):
        cx = self.rt.new_context()
        cx.set_access(access_checker)

        cx.add_global('params', params)
        for qtype, qtypeobj in queries.query_types:
            cx.add_global(qtype, qtypeobj)
        cx.add_global('Search', queries.Search)
        cx.add_global('HttpError', JsHttpError)
        res = cx.execute(tmpl)

        if isinstance(res, JsHttpError):
            raise wsgiwapi.HTTPError(res.code, body=res.body)
        if not isinstance(res, queries.Search):
            raise wsgiwapi.HTTPError(400, "Template didn't return a Search.")

        return res
