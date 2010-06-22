# Copyright (c) 2010 Lemur Consulting Ltd
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

r"""Minimal helper classes for adding Flax functions to Xapian, without
trying to abstract or hide the Xapian API.

See flaxcode/applications/xml_indexer and simple_search for examples of how
to use Flax Core.

"""

import time
from datetime import datetime
import re
import xapian
try:
    import json
except ImportError:
    import simplejson as json

from errors import FieldmapError, IndexingError, SearchError

# adapt facet code for version of Xapian
try:
    _FacetMatchSpy = xapian.MultiValueCountMatchSpy
    _multivalues = True
except AttributeError:
    _FacetMatchSpy = xapian.ValueCountMatchSpy
    _multivalues = False


class Fieldmap(object):
    """Helper class for adding named field functionality to Xapian.
    
    Supports indexing, easy query construction and search with facets.
    
    """
    
    def __init__(self, database=None, language=None):
        """Init a new fieldmap.
        
        If `database` is supplied, the map will be inited using the values
        stored in the database, if any. Note that the database object is
        not part of the Fieldmap state.
        
        If `language` is supplied, free-text fields will be stemmed using
        the appropriate stemmer (if available) for indexing and retrieval.
        
        """
        self._fieldmap = {}
        self.language = language
        if database:
            # FIXME: handle conflict between saved and supplied arguments?
            self.language = database.get_metadata('flax.language') or None
            jstr = database.get_metadata('flax.fieldmap')
            if jstr:
                for k, v in json.loads(jstr).iteritems():
                    self._fieldmap[k] = tuple(v)

    def save(self, database):
        """Save this fieldmap to the database specified.
        
        `database` must be a xapian.WritableDatabase
        
        """
        database.set_metadata('flax.fieldmap', json.dumps(self._fieldmap))
        database.set_metadata('flax.language', self.language)

    def setfield(self, fieldname, isfilter, overwrite=False):
        """Set a field in the map.
        
        `fieldname` is the name of the field.
        `isfilter` should be True iff the field is a filter.
        `overwrite` must be true to overwrite an existing definition.
        
        """
        fieldname = unicode(fieldname)
        if self._fieldmap.get(fieldname) and not overwrite:
            raise FieldmapError, 'field "%s" already exists' % fieldname

        if self._fieldmap:
            fieldnum = 1 + max(x[1] for x in self._fieldmap.itervalues())
        else:
            fieldnum = 0
            
        self._fieldmap[fieldname] = (
            self._make_prefix(fieldnum), fieldnum, isfilter)

    def _make_prefix(self, fieldnum):
        al = u'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        ret = []
        while True:
            ret.insert(0, al[fieldnum % 26])
            fieldnum /= 26
            if fieldnum == 0: break
        
        ret.insert(0, 'X')
        return ''.join(ret)
    
    def __getitem__(self, key):
        """Return settings for a field, as (prefix, value_number, isfilter)
        
        """
        return self._fieldmap[key]

    def __iter__(self):
        """Iterate over the fields.
        
        """
        return self._fieldmap.iteritems()
    
    def __eq__(self, other):
        return self._fieldmap == other._fieldmap
        
    def __str__(self):
        return 'Fieldmap: %r' % self._fieldmap

    def query_parser(self, database=None):
        """Return a xapian.QueryParser object set up for this fieldmap.
        
        `database` should be supplied if you want to use spelling correction etc.
        
        """
        
        
        qp = xapian.QueryParser()
        if database:
            qp.set_database(database)

        if self.language:
            qp.set_stemmer(xapian.Stem(self.language))
        
        # add fieldname prefixes
        for name, (prefix, valnum, isfilter) in self._fieldmap.iteritems():
            if isfilter:
                qp.add_boolean_prefix(name, prefix)
            else:
                qp.add_prefix(name, prefix)

        return qp

    def query(self, fieldname, value, weight=None, op=xapian.Query.OP_OR):
        """Return a xapian.Query constructed from the data supplied.
        
        `fieldname` is the field to search.
        `value` is the value to search for. This can be a string, an int, a
            float, a datetime, or an iterable of any of these. The fieldmap
            will try to handle each case appropriately.
        `weight` is an optional weight to apply to the query.
        `op` is the xapian.Query operator to use to combine sequence values
            (default is OR).
        
        """
        prefix, valnum, isfilter = self._fieldmap[fieldname]

        def mq(v):
            if isinstance(v, unicode):
                v = v.encode('utf-8', 'ignore')
            
            if isinstance(v, str):
                return xapian.Query('%s%s%s' % (prefix, 
                    ':' if v[0].isupper() else '', v))
            elif isinstance(v, int) or isinstance(v, float):
                strv = xapian.sortable_serialise(v)
                return xapian.Query(
                    xapian.Query.OP_VALUE_RANGE, valnum, strv, strv)
            elif isinstance(v, datetime):                
                term = '%s%04d%02d%02d' % (prefix, v.year, v.month, v.day)
                strv = '%04d%02d%02d%02d%02d%02d' % (
                    v.year, v.month, v.day, v.hour, v.minute, v.second)
                return xapian.Query(xapian.Query.OP_AND,
                    xapian.Query(term), xapian.Query(
                        xapian.Query.OP_VALUE_RANGE, valnum, strv, strv))
            else:
                raise SearchError, 'unexpected type (%s) for value %s' % (
                    type(v), v)

        def apply_weight(q):
            if weight is not None:
                return xapian.Query(xapian.Query.OP_SCALE_WEIGHT, q, weight)
            else:
                return q

        if isinstance(value, list) or isinstance(value, tuple):
            return apply_weight(xapian.Query(op, [mq(v) for v in value]))
        else:
            return apply_weight(mq(value))

    def range_query(self, fieldname, value1, value2):
        """Construct a xapian.Query object representing a value range.
        
        `fieldname` is the field to search.
        `value1` and `value2` define the range, inclusively.
        
        The values must be of the same type (int, float or datetime). In the
        latter case, the fieldmap will generate helper terms to try to
        optimise the query.
        
        """
        if type(value1) is not type(value2):
            raise SearchError, 'cannot mix types in a query range'

        try:
            prefix, valnum, isfilter = self._fieldmap[fieldname]
        except KeyError:
            raise SearchError, 'fieldname %s not in fieldmap' % fieldname

        if isinstance(value1, int) or isinstance(value1, float):
            return xapian.Query(xapian.Query.OP_VALUE_RANGE, valnum,
                xapian.sortable_serialise(value1), 
                xapian.sortable_serialise(value2))
                
        elif isinstance(value1, datetime):
#            term = '%s%04d%02d%02d' % (prefix, v.year, v.month, v.day)
#            strv = '%04d%02d%02d%02d%02d%02d' % (
#                v.year, v.month, v.day, v.hour, v.minute, v.second)
#           FIXME - helper terms
            return xapian.Query(xapian.Query.OP_VALUE_RANGE, valnum, 
                strv, strv))

    @staticmethod
    def _combine(op, query1, query2):
        if query1:
            if query2:
                return xapian.Query(op, query1, query2)
            else:
                return query1
        else:
            return query2

    @staticmethod
    def AND(query1, query2):
        """Combine two xapian.Query objects with AND.
        
        For convenience, either query can be None, in which case the other
        query will be returned.
        
        """
        return Fieldmap._combine(xapian.Query.OP_AND, query1, query2)

    @staticmethod
    def OR(query1, query2):
        """Combine two xapian.Query objects with OR (see AND).
        
        """
        return Fieldmap._combine(xapian.Query.OP_OR, query1, query2)

    @staticmethod
    def XOR(query1, query2):
        """Combine two xapian.Query objects with XOR (see AND).
        
        """
        return Fieldmap._combine(xapian.Query.OP_XOR, query1, query2)

    @staticmethod
    def AND_NOT(query1, query2):
        """Combine two xapian.Query objects with AND_NOT (see AND).
        
        """
        return Fieldmap._combine(xapian.Query.OP_AND_NOT, query1, query2)

    @staticmethod
    def AND_MAYBE(query1, query2):
        """Combine two xapian.Query objects with AND_MAYBE (see AND).
        
        """
        return Fieldmap._combine(xapian.Query.OP_AND_MAYBE, query1, query2)

    @staticmethod
    def FILTER(query1, query2):
        """Combine two xapian.Query objects with FILTER (see AND).
        
        """
        return Fieldmap._combine(xapian.Query.OP_FILTER, query1, query2)
    
    def document(self):
        """Return a Flax document object.

        This is a thin wrapper for a xapian.Document to support Flax indexing.
        
        """
        return _FlaxDocument(self._fieldmap, self.language)
        
    @staticmethod
    def add_document(database, doc):
        """Add a document to a database.
        
        `database` is a xapian.WritableDatabase
        `doc` is a Flax document
        
        Convenience method. If `doc` has a non-None `_docid` attr, this will 
        be used as the document ID, and it will replace any document with the
        same ID.
        
        """
        if doc._docid is not None:
            database.replace_document(doc._docid, doc.get_xapian_doc())            
        else:
            database.add_document(doc.get_xapian_doc())

    def search(self, database, query, startrank=0, maxitems=20, 
               facet_fields=[], maxfacets=100, checkatleast=100):
        """Search a database, returning hits and facets.
        
        `database` is a xapian.Database.
        `query` is a xapian.Query.
        `startrank` is the rank of the first hit to return.
        `maxitems` is the maximum number of hits to return.
        `facet_fields` is an iterable of fieldnames to collect facets for
            (note that these must be filter fields in the fieldmap).
        `maxfacets` is the maximum number of facet values to return for 
            each facet field.
        `checkatleast` is the minimum number of documents to check
        
        Results are returned as a xapian.MSet, with an additional attribute
        `facets` containing the facets collected as a dict.
        
        FIXME - how to use MatchDeciders, Sorters etc ?
        FIXME - stopwords?

        """
        enq = xapian.Enquire(database)
        enq.set_query(query)

        # set up matchspies for facets
        matchspies = []
        for field in facet_fields:        
            ms = _FacetMatchSpy(self._fieldmap[field][1])
            enq.add_matchspy(ms)
            matchspies.append((field, ms))

        mset = enq.get_mset(startrank, maxitems, checkatleast)
    
        # collect facets
        facets = {}
        if _multivalues:
            for field, ms in matchspies:
                facets[field] = [x[0] for x in ms.get_top_values(maxfacets)]
        else:
            for field, ms in matchspies:
                facets[field] = [x.term for x in ms.top_values(maxfacets)]
        
        # this is ok in Python, but what about other languages?
        mset.facets = facets
        return mset
        

class _FlaxDocument(object):
    """A wrapper for Xapian documents with convenience functions for indexing.
    
    """

    def __init__(self, fieldmap, language):
        self._fieldmap = fieldmap
        self._doc = xapian.Document()
        self._stemmer = xapian.Stem(language) if language else None
        self._facets = {}
        self._docid = None
        self.database = None

    @property
    def fieldmap(self):
        return self._fieldmap
    
    def clear_docid(self):
        self._docid = None
    
    def index(self, fieldname, value, search_default=False,
              store_facet=True, spelling=False, weight=1, isdocid=False):
        """Index a field value.
        
        `fieldname` is the field to index.
        `value` is the value to index. This can be a string, int, float, or
            datetime object. Flax will attempt to index each appropriately.
            This should either be a unicode object or a UTF-8 string.
        `store_facet` specifies whether to store facet values (filter fields
            only) and is True by default.
        `spelling` specifies whether to add spellings to the database.
        `weight` allows the WDF to be set (1 by default)
        `isdocid` uses this field value as a docid (filter fields only).
            False by default.
        
        """

        if not value:
            return
        
        if isdocid and self._docid:
            raise IndexingError, 'docid has already been set'
        
        if isinstance(value, unicode):
            value = value.encode('utf-8', 'ignore')

        prefix, valnum, isfilter = self._fieldmap[fieldname]
    
        if not isfilter or search_default or spelling:
            termgen = xapian.TermGenerator()
            if self._stemmer:
                termgen.set_stemmer(self._stemmer)
        
        if isfilter:
            if isinstance(value, basestring):
                term = u'%s%s%s' % (prefix, ':' if value[0].isupper() else '', 
                       value.decode('utf-8', 'ignore'))
                term = term.encode('utf-8', 'ignore')
                if isinstance(value, unicode):
                    value = value.encode('utf-8', 'ignore')
                
                self._doc.add_term(term)

                if store_facet:
                    if _multivalues:
                        self._facets.setdefault(valnum,
                            xapian.StringListSerialiser()).append(value)
                    else:
                        if self._facets.get(valnum):
                            raise IndexingError, \
                                'facet value already set for "%s" field' % fieldname
                        self._facets[valnum] = value

                if isdocid:
                    self._docid = term
                    
            elif isinstance(value, float) or isinstance(value, int):
                self._doc.add_value(valnum, xapian.sortable_serialise(value))
                # FIXME - helper terms?
                # FIXME - numeric facets

                if isdocid:
                    self._docid = '%s%s' % (prefix, value)

            elif isinstance(value, datetime):            
                self._doc.add_term('%s%04d' % (prefix, value.year))
                self._doc.add_term('%s%04d%02d' % (prefix, 
                    value.year, value.month))
                self._doc.add_term('%s%04d%02d%02d' % (prefix, 
                    value.year, value.month, value.day))                    
#                self._doc.add_value(valnum, '%04d%02d%02d%02d%02d%02d' % (
#                    value.year, value.month, value.day, 
#                    value.hour, value.minute, value.second))
                self._doc.add_value(valnum, xapian.sortable_serialise(
                    time.mktime(value.timetuple())))
                    
                if isdocid:
                    raise IndexingError, 'cannot use date as docid'
        else:                
            if isinstance(value, str):
                termgen.set_document(self._doc)
                termgen.index_text(value, weight, prefix)
            else:
                raise IndexingError, 'non-filter field requires string value'

            if isdocid:
                raise IndexingError, 'cannot use non-filter field as docid'

        # spelling only works for prefix-less terms
        if search_default or spelling:
            if search_default:
                termgen.set_document(self._doc)
            else:
                termgen.set_document(xapian.Document())  # dummy document

            if spelling:
                if self.database is None:
                    raise IndexingError, 'spelling requires document.database to be set'
                termgen.set_database(self.database)
                termgen.set_flags(termgen.FLAG_SPELLING)

            termgen.index_text(value)

    def set_data(self, data):
        """Set the document data. This does no indexing.
        
        """
        self._doc.set_data(data)
    
    def get_xapian_doc(self):
        """Return a xapian.Document for this Flax document.
        
        """
        if _multivalues:
            # serialise and add facet values
            for slot, serialiser in self._facets.iteritems():
                self._doc.add_value(slot, serialiser.get())
        else:
            for slot, value in self._facets.iteritems():
                self._doc.add_value(slot, value)
        
        return self._doc

def run_tests():    
    """Run some tests. These look at internal values, so are not really
    a good example of how to use fieldmaps.
    
    """

    db = xapian.WritableDatabase('/tmp/flaxtest.db', xapian.DB_CREATE_OR_OVERWRITE)

    # set up a fieldmap
    fm = Fieldmap()
    fm.language = 'en'              # stem for English
    fm.setfield('foo', False)       # text field
    fm.setfield('bar', True)        # filter field
    fm.setfield('spam', False)
    fm.setfield('eggs', True)

    fm.save(db)                     # save fieldmap to database
    
    # create a new document and set some data
    doc = fm.document()
    doc.database = db
    doc.set_data({'data': 'any data we like'})
    
    # index some fields
    doc.index('foo', 'gruyere cheese fondue', search_default=True, spelling=True)
    doc.index('bar', 'chips')
    try:
        doc.index('bar', 'crisps')
    except IndexingError:
        if _multivalues: raise
        
    doc.index('spam', 'carrot cake')
    doc.index('eggs', datetime(2010, 2, 3, 12, 0))

    # TEST - do we have expected terms?
    xdoc = doc.get_xapian_doc()
    terms = [t.term for t in xdoc]
    for test in ['XAcheese', 'ZXAchees', 'XCcake',
                 'Zgruyer', 'gruyere', 'Zchees', 'cheese',
                 'XD2010', 'XD201002', 'XD20100203']:
        assert test in terms, 'term %s is missing' % test

    # TEST - do we have expected values?
    if _multivalues:
        tmp = xapian.StringListUnserialiser(xdoc.get_value(1))
        assert tmp.get() == 'chips'
        tmp.next()
        assert tmp.get() == 'crisps'
    else:
        assert xdoc.get_value(1) == 'chips'
        
    assert xdoc.get_value(3) == '20100203120000'
    
    # add document to database (if doc.docid was set, this will overwrite any
    # document with the same ID)
    fm.add_document(db, doc)
    db.flush()
    
    qp = fm.query_parser()
    
    # TEST - does it work as expected?
    query = qp.parse_query('tea bar:coffee foo:gin')
    assert str(query) == 'Xapian::Query(((tea:(pos=1) OR XAgin:(pos=2)) FILTER XBcoffee))'

    # TEST - some other queries
    q1 = fm.OR(fm.query('foo', 'cheese'), fm.query('foo', 'tofu'))    
    q2 = fm.query('foo', ('cheese', 'tofu'))
    assert str(q1) == str(q2)

    # TEST - search and facets
    mset = fm.search(db, q1, facet_fields=['bar'])
    assert mset.get_matches_estimated() == 1
    if _multivalues:
        assert mset.facets['bar'] == ['chips', 'crisps']
    else:
        assert mset.facets['bar'] == ['chips']

    # TEST - another query test with a query branch weight adjustment    
    q2 = fm.AND(fm.query('bar', 'chips'), fm.query('bar', 'chaps', 0.5))
    assert str(q2) == 'Xapian::Query((XBchips AND 0.5 * XBchaps))'
    
    # TEST spelling
    spellings = [t.term for t in db.spellings()]
    assert spellings == ['cheese', 'fondue', 'gruyere']
    
    print 'all tests passed'

if __name__ == '__main__':
    run_tests()
