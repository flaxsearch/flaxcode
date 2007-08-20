# $Id$
# dummy - enough structure just to drive the web interface.

class collection(object):

    __slots__ = ("name", "description", "filespec", "schedule", "db")
                 
    def __init__(self, name):
        self.name=name
        self.description = ""
        self.filespec = self.schedule = self.db = None

class collections(object):

    def __init__(self):
        self._collections = {}

    def new_collection(self, name):
        if type(name) == str and not self._collections.has_key(name):
            col = collection(name)
            self._collections[name] = col
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
        
    def __iter__(self):
        return self._collections.itervalues()

