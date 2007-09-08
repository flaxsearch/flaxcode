# $Id$
# dummy - enough structure just to drive the web interface.
from __future__ import with_statement
import os
import sys
sys.path = [os.path.normpath(os.path.join(__file__, '..', '..','libs', 'xappy'))]+sys.path
import xappy
import filespec

_root_dir = os.path.dirname(os.path.abspath(os.path.normpath(__file__)))+'/dbs'

class collection(object):

    _stopwords = ('i', 'a', 'an', 'and', 'the')

    def __init__(self, name):
        self.name=name
        self.description = ""
        self.indexed = 0
        self.queries = 0
        self.docs = 0
        self.status = 0
        self.paths=[]
        self.exclusions = []
        self.earliest = self.latest = self.youngest = self.oldest = None
        self.formats = ["txt", "html", "doc"]
        self.update_filespec()
        self.update_connection()

    def update(self, **kwargs):
        self.__dict__.update(kwargs)
        self.update_filespec()
        self.update_connection()

    def update_filespec(self):
        self._filespec = filespec.FileSpec(paths = self.paths,
                                           exclusions = self.exclusions,
                                           earliest = self.earliest,
                                           latest = self.latest,
                                           youngest = self.youngest,
                                           oldest = self.oldest,
                                           formats = self.formats)
                                           
    def dbname(self):
        return os.path.join(_root_dir, self.name+'.db')
            
    def process_file(self, file_name):
        print "processing file: ", file_name
        with open(file_name) as f:
            doc = xappy.UnprocessedDocument()
            doc.fields.append(xappy.Field('text', f.read()))
            pdoc = self._conn.process(doc)
            self._conn.add(pdoc)
                
    def make_xapian_db(self):
        self._conn = xappy.IndexerConnection(self.dbname())
        for f in self._filespec.files():
            print f
            self.process_file(f)
        self._conn.flush()
        self._conn.close()
        
    def update_connection(self):
        dbname = self.dbname()
        self._conn = xappy.IndexerConnection(dbname)
        self._conn.add_field_action ('text', xappy.FieldActions.INDEX_FREETEXT, 
                                     language='en', stop=self._stopwords, noprefix=True)
        self._conn.add_field_action ('text', xappy.FieldActions.STORE_CONTENT)
        
        self._conn.close()

    def search(self, query):
        db = xappy.SearchConnection(self.dbname())
        query = db.query_parse(query.lower())
        print query
        return db.search(query, 0, 10)
                                 
class collections(object):

    def __init__(self):
        self._collections = {}
        self._formats = ["txt", "html", "doc"]

    def new_collection(self, name, **kwargs):
        if type(name) == str and not self._collections.has_key(name):
            col = collection(name)
            self._collections[name] = col
            col.__dict__.update(kwargs)
            return col
        else:
            # error
            pass

    def remove_collection(self, name):
        if type(name) == str and self._collections.has_key(name):
            del self._collections[name]
        else:
            #error
            pass

    def __getitem__(self, key):
        return self._collections.__getitem__(key)

    def __setitem__(self, key, val):
        self._collections.__setitem__(key, val)

    def __contains__(self, key):
        return self._collections.__contains__(key)

    def __iter__(self):
        return self._collections.__iter__()

    def iterkeys(self):
        return self._collections.iterkeys()

    def iteritems(self):
        return self._collections.iteritems()

    def itervalues(self):
        return self._collections.itervalues()

        
