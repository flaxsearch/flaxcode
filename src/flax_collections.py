import doc_collection
import util
util.setup_sys_path()
import xappy
import xapian  # HACK

class FlaxCollections(object):

    def __init__(self, db_dir):
        self._collections = {}
        self.db_dir = db_dir
        self._formats = ["txt", "html", "doc"]

    def new_collection(self, name, **kwargs):
        if type(name) == str and not self._collections.has_key(name):
            col = doc_collection.DocCollection(name, self.db_dir)
            self._collections[name] = col
            col.update(**kwargs)
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

    def search(self, query, cols = None, tophit = 0, maxhits = 10):
        if cols is None:
            cols = self._collections.keys()
        
        if cols:
            col = self[cols[0]]
            conn = xappy.SearchConnection(col.dbname())
            for c in cols[1:]:
                conn._index.add_database(xapian.Database(self[c].dbname()))
            query = conn.query_parse(query)
            return conn.search (query, tophit, tophit + maxhits)
        else:
            return []

    @property
    def collection_names (self):
        return self._collections.keys()

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

        
