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
r"""Abstract definitions of queries and searches.

These are parsed from the search call parameters, and passed to the backends.

"""
__docformat__ = "restructuredtext en"

query_types = []

class QueryMetaClass(type):
    """Metaclass for Query objects.

    Keeps a registry of all defined Query types.

    """
    def __init__(self, class_name, bases, namespace):
        query_types.append((class_name, self))
        query_types.sort()

class Query(object):
    """Base class of all queries.

    All queries have the "op" member, which is used to identify the type
    of the query.

    """
    __metaclass__ = QueryMetaClass
    op = None

    def __repr__(self):
        return "Query()"

    # Constants used to represent the operators.
    OR = 0
    AND = 1
    XOR = 2
    NOT = 3
    TEXT = 4

    # The names of the operators, in order.
    OP_NAMES = ('OR', 'AND', 'XOR', 'NOT', 'TEXT', )

    @staticmethod
    def opname(op):
        """Get the textual name of an operator from its code.

        """
        return OP_NAMES[op]

    @staticmethod
    def compose(op, queries):
        """Compose a set of queries by with the specified operator.

        The allowed operators are:

         - 'OR': documents match if any queries match.
         - 'AND': documents only match if all queries match.
         - 'XOR': documents match if exactly one of the subqueries match.
         - 'ANDNOT', (or the synonym 'ANDNOT'): documents match only if the
           first query matches, and none of the other queries match.

        """
        if len(queries) < 2:
            if len(queries) == 0:
                return Query()
            else:
                return queries[0]

        if not isinstance(other, (Query, xapian.Query)):
            return NotImplemented

class QueryOr(Query):
    """A query which matches a document if any of its subqueries match.

    The weights for the returned query will be the sum of the weights of the
    subqueries which match.

    """
    op = Query.OR
    def __init__(self, subqs):
        self.subqs = subqs
    def __repr__(self):
        return "QueryOr(%r)" % self.subqs

class QueryAnd(Query):
    """A query which matches a document if all of its subqueries match.

    The weights for the returned query will be the sum of the weights of the
    subqueries.

    """
    op = Query.AND
    def __init__(self, subqs):
        self.subqs = subqs
    def __repr__(self):
        return "QueryAnd(%r)" % self.subqs

class QueryXor(Query):
    """A query which matches a document if exactly one of its subqueries match.

    The weights for the returned query will be the sum of the weights of the
    subqueries which match.

    """
    op = Query.XOR
    def __init__(self, subqs):
        self.subqs = subqs
    def __repr__(self):
        return "QueryXor(%r)" % self.subqs

class QueryNot(Query):
    """A query which matches a document if its first subquery matches but none
    of its other subqueries do.

    The weights for the returned query will be the weights of the first
    subquery.

    """
    op = Query.NOT
    def __init__(self, subqs):
        if len(subqs) > 2:
            subqs = (subqs[0], QueryOr(subqs[1:]))
        self.subqs = subqs
    def __repr__(self):
        return "QueryNot(%r)" % self.subqs

class QueryText(Query):
    """A free-text query for a piece of text.

    """
    op = 'text'

    def __init__(self, text, fields=None):
        self.text = text
        self.fields = fields

    def __repr__(self):
        return "QueryText(%r)" % self.text

class Search(object):
    def __init__(self, query, start_rank, end_rank):
        self.query = query
        self.start_rank = start_rank
        self.end_rank = end_rank
        self.percent_cutoff = None

    def __repr__(self):
        r = "%r, %d, %d" % (self.query, self.start_rank, self.end_rank)
        if self.percent_cutoff is not None and self.percent_cutoff > 0:
            r += ", %d" % self.percent_cutoff
        return "Search(" + r + ")"
