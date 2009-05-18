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
r"""Test operations on the query abstraction.

"""
__docformat__ = "restructuredtext en"

from harness import *

from flax.searchserver import queries

class AbstractQueryTest(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_query1(self):
        qnames = [q[0] for q in queries.query_types]
        self.assertEqual(qnames,
            ['Query', 'QueryAnd', 'QueryMultWeight', 'QueryNot', 'QueryOr',
             'QueryText', 'QueryXor',
            ])

        q = queries.Query()
        self.assertEqual(unicode(q), u'Query()')

        q = queries.QueryText('hello')
        self.assertEqual(unicode(q), u'QueryText(\'hello\')')

        q = q * 2
        self.assertEqual(unicode(q), u'(QueryText(\'hello\') * 2)')

        q2 = q & q
        self.assertEqual(unicode(q2), u'(QueryText(\'hello\') * 2) & (QueryText(\'hello\') * 2)')

        q2 = q | q
        self.assertEqual(unicode(q2), u'(QueryText(\'hello\') * 2) | (QueryText(\'hello\') * 2)')

        q2 = q ^ q
        self.assertEqual(unicode(q2), u'(QueryText(\'hello\') * 2) ^ (QueryText(\'hello\') * 2)')

        q2 = q - q
        self.assertEqual(unicode(q2), u'(QueryText(\'hello\') * 2) - (QueryText(\'hello\') * 2)')


if __name__ == '__main__':
    main()
