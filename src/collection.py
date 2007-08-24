# $Id$
# dummy - enough structure just to drive the web interface.

class collection(object):

    def __init__(self, name):
        self.name=name
        self.description = ""
        self.indexed = 0
        self.queries = 0
        self.docs = 0
        self.status = 0
        self.paths=[]
        self.formats = ["txt", "html", "doc"]


class collections(object):

    def __init__(self):
        self._collections = {}

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

