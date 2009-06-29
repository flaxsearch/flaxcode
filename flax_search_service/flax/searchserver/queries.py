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

class Query(object):
    """Base class of all queries.

    All queries have the "op" member, which is used to identify the type
    of the query.

    """
    op = None

    def __unicode__(self):
        return u"Query()"

    def __repr__(self):
        return u"Query()"

    # Constants used to represent the operators.
    OR = 0
    AND = 1
    XOR = 2
    NOT = 3
    MULTWEIGHT = 4
    TEXT = 5
    EXACT = 6
    SIMILAR = 7

    # The names of the operators, in order.
    OP_NAMES = (u'OR', u'AND', u'XOR', u'NOT',
                u'MULTWEIGHT', u'TEXT',
                u'EXACT', u'SIMILAR',)

    # Symbols representing the operators, in order.  None if no symbol.
    OP_SYMS = (u'|', u'&', u'^', u'-',
               None, None,
               None, None,)

    @staticmethod
    def opname(op):
        """Get the textual name of an operator from its code.

        """
        return Query.OP_NAMES[op]

    @staticmethod
    def opsym(op):
        """Get the symbol for an operator from its code.

        """
        return Query.OP_SYMS[op]

    @staticmethod
    def compose(op, queries):
        """Compose a set of queries with the specified operator.

        The allowed operators are:

         - 'OR': documents match if any queries match.
         - 'AND': documents only match if all queries match.
         - 'XOR': documents match if exactly one of the subqueries match.
         - 'NOT', (or the synonym 'ANDNOT'): documents match only if the
           first query matches, and none of the other queries match.

        The operator may be specified by using one of the exact strings above,
        or by using one of the corresponding constants on the Query class
        (Query.OR, Query.AND, Query.XOR, Query.NOT).

        """
        if len(queries) < 2:
            if len(queries) == 0:
                return Query()
            else:
                return queries[0]

        for query in queries:
            if not isinstance(query, Query):
                raise TypeError("Object supplied to Query.compose() "
                                "was not a Query.")

        return {
            Query.OR: QueryOr,
            Query.AND: QueryAnd,
            Query.XOR: QueryXor,
            Query.NOT: QueryNot,
            "OR": QueryOr,
            "AND": QueryAnd,
            "XOR": QueryXor,
            "NOT": QueryNot,
            "ANDNOT": QueryNot,
        }[op](queries)

    def __mul__(self, mult):
        """Return a query with the weight scaled by multiplier.

        """
        try:
            return QueryMultWeight(self, mult)
        except TypeError:
            return NotImplemented

    def __rmul__(self, lhs):
        """Return a query with the weight scaled by multiplier.

        """
        return self.__mul__(lhs)

    def __div__(self, rhs):
        """Return a query with the weight divided by a number.

        """
        try:
            return self.__mul__(1.0 / rhs)
        except TypeError:
            return NotImplemented

    def __truediv__(self, rhs):
        """Return a query with the weight divided by a number.

        """
        try:
            return self.__mul__(1.0 / rhs)
        except TypeError:
            return NotImplemented

    def __and__(self, other):
        """Return a query combined using AND with another query.

        """
        if not isinstance(other, Query):
            return NotImplemented
        return QueryAnd((self, other))

    def __or__(self, other):
        """Return a query combined using OR with another query.

        """
        if not isinstance(other, Query):
            return NotImplemented
        return QueryOr((self, other))

    def __xor__(self, other):
        """Return a query combined using XOR with another query.

        """
        if not isinstance(other, Query):
            return NotImplemented
        return QueryXor((self, other))

    def __sub__(self, other):
        """Return a query combined using XOR with another query.

        """
        if not isinstance(other, Query):
            return NotImplemented
        return QueryNot((self, other))

class QueryCombination(Query):
    """A query which represents a combination of other queries.

    """
    def __init__(self, subqs):
        self.subqs = list(subqs)
        for query in self.subqs:
            if not isinstance(query, Query):
                raise TypeError("Object supplied to QueryCombination() "
                                "was not a Query.")

    def __unicode__(self):
        joinsym = u' ' + Query.opsym(self.op) + u' '
        return u'(' + joinsym.join(unicode(q) for q in self.subqs) + u')'

    def __repr__(self):
        joinsym = ' ' + Query.opsym(self.op) + ' '
        return '(' + joinsym.join(__repr__(q) for q in self.subqs) + ')'

class QueryOr(QueryCombination):
    """A query which matches a document if any of its subqueries match.

    The weights for the returned query will be the sum of the weights of the
    subqueries which match.

    """
    op = Query.OR

class QueryAnd(QueryCombination):
    """A query which matches a document if all of its subqueries match.

    The weights for the returned query will be the sum of the weights of the
    subqueries.

    """
    op = Query.AND

class QueryXor(QueryCombination):
    """A query which matches a document if exactly one of its subqueries match.

    The weights for the returned query will be the sum of the weights of the
    subqueries which match.

    """
    op = Query.XOR

class QueryNot(QueryCombination):
    """A query which matches a document if its first subquery matches but none
    of its other subqueries do.

    The weights for the returned query will be the weights of the first
    subquery.

    """
    op = Query.NOT
    def __init__(self, subqs):
        if len(subqs) > 2:
            subqs = (subqs[0], QueryOr(subqs[1:]))
        QueryCombination.__init__(self, subqs)

class QueryMultWeight(Query):
    """A query which returns the same documents as a sub-query, but with the
    weights multiplied by the given number.

    """
    op = Query.MULTWEIGHT
    def __init__(self, subq, mult):
        self.subq = subq
        self.mult = float(mult)
    def __unicode__(self):
        return u"(%s * %.4g)" % (unicode(self.subq), self.mult)
    def __repr__(self):
        return "(%s * %.4g)" % (repr(self.subq), self.mult)

class QueryText(Query):
    """A free-text query for a piece of text.

    """
    op = Query.TEXT
    def __init__(self, text, fields=None, default_op=Query.AND):
        """Create a free-text query.

        - `text` is the text to search for - must be unicode.
        - `fields` is an iterable holding a list of fields to search in.
        - `default_op` is the default operator to use in the search, and is
          either Query.AND or Query.OR.

        """
        if not isinstance(text, unicode):
            raise TypeError("Text supplied was not unicode")
        if default_op not in (Query.AND, Query.OR,):
            raise TypeError("Operator must be either Query.AND or Query.OR")

        self.text = text
        self.fields = fields
        self.default_op = default_op

    def __unicode__(self):
        return u"QueryText(%r)" % (self.text, )
    def __repr__(self):
        return "QueryText(%r)" % (self.text, )

class QueryExact(Query):
    """A query which returns documents containing the exact field contents.

    """
    op = Query.SIMILAR
    def __init__(self, text, fields=None):
        """Create an exact field search.

        """
        if not isinstance(text, unicode):
            raise TypeError("Text supplied was not unicode")

        self.text = text
        self.fields = fields

    def __unicode__(self):
        return u"QueryExact(%r, %r)" % (self.text, self.fields, )
    def __repr__(self):
        return "QueryExact(%r, %r)" % (self.text, self.fields, )

class QuerySimilar(Query):
    """A query which returns similar documents to a given set of documents.

    """
    op = Query.SIMILAR
    def __init__(self, ids, simterms=20):
        """Create a similarity query.

        The similarity query returns documents which are similar to those
        supplied.

        - `ids` is an iterable holding a list of document ids to find similar
          items to.
        - `simterms` is a suggestion for the number of terms to use in the
          similarity calculation.  Backends may ignore this, or treat it only
          as a recommendation.

        """
        self.ids = list(ids)
        self.simterms = int(simterms)

    def __unicode__(self):
        return u"QuerySimilar(%r)" % (self.ids, )
    def __repr__(self):
        return "QuerySimilar(%r)" % (self.ids, )

class Search(object):
    def __init__(self, query, start_rank, end_rank, percent_cutoff=None,
                 summary_fields=None, summary_maxlen=None, summary_hl=None):

        self.query = query
        self.start_rank = start_rank
        self.end_rank = end_rank
        self.percent_cutoff = percent_cutoff

        self.summary_fields = summary_fields
        self.summary_maxlen = summary_maxlen
        self.summary_hl = summary_hl

    def __unicode__(self):
        r = u"%r, %d, %d" % (self.query, self.start_rank, self.end_rank)
        if self.percent_cutoff is not None and self.percent_cutoff > 0:
            r += u", %d" % self.percent_cutoff
        return u"Search(%s)" % r
    def __repr__(self):
        r = "%r, %d, %d" % (self.query, self.start_rank, self.end_rank)
        if self.percent_cutoff is not None and self.percent_cutoff > 0:
            r += ", %d" % self.percent_cutoff
        return "Search(%s)" % r


query_types = 'Query,QueryOr,QueryAnd,QueryXor,QueryNot,' \
              'QueryMultWeight,QueryText,' \
              'QueryExact,QuerySimilar'
query_types = [(q, globals()[q]) for q in query_types.split(',')]
query_types.sort()
