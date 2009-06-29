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
r"""Test creation and deletion of databases

"""
__docformat__ = "restructuredtext en"

from harness import *
from flax.searchserver import jstemplates, queries

class JSQueryTemplateTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_jsquery1(self):
        evaluator = jstemplates.JsTemplateEvaluator()
        self.assertRaisesMessage(wsgiwapi.HTTPError,
                                 u"^400 Bad Request\nTemplate didn't return a Search\.$",
                                 evaluator.search_template,
                                 '', {}
                                )

        s = evaluator.search_template('Search(Query(), 0, 0)', {})
        self.assertEqual(unicode(s), u'Search(Query(), 0, 0)')

        s = evaluator.search_template('q = QueryText("foo"); Search(q, 0, 0)', {})
        self.assertEqual(unicode(s), u'Search(QueryText(u\'foo\'), 0, 0)')

if __name__ == '__main__':
    main()
