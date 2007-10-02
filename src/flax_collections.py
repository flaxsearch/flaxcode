import logging
import doc_collection
import search
import util
util.setup_sys_path()

log = logging.getLogger("collection")

class FlaxCollections(object):

    def __init__(self, db_dir):
        self._collections = {}
        self.db_dir = db_dir
        self._formats = ["txt", "html", "doc"]

    def new_collection(self, name, **kwargs):
        if type(name) == str and not self._collections.has_key(name):
            log.info("Creating new collection: %s" % name)
            col = doc_collection.DocCollection(name, self.db_dir)
            self._collections[name] = col
            col.update(**kwargs)
            return col
        else:
            log.error("Failed attempt to create collection: %s" % name)

    def remove_collection(self, name):
        if type(name) == str and self._collections.has_key(name):
            log.info("Deleting collection %s" % name)
            del self._collections[name]
        else:
            log.error("Failed attempt to delete collection %s" % name)

    def search(self, query, cols = None, tophit = 0, maxhits = 10):
        if cols is None:
            cols = self._collections.keys()
            
        if cols:
            dbs_to_search = [self._collections[col].dbname() for col in cols]
            return search.search(dbs_to_search, query, tophit, maxhits)
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

        
