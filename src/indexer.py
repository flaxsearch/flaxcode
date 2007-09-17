from __future__ import with_statement
import Pyro.core
import Pyro.naming
import filespec
import util
util.setup_sys_path()
import xappy

class Indexer(Pyro.core.ObjBase):
    
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)

    def do_indexing(self, file_spec, dbname):
        print "Indexing xapian db: %s, with files from filespec %s:" % (dbname, file_spec)
        self.refresh_xapian_db(dbname, file_spec)
        print "Indexing Finished"

    def refresh_xapian_db(self, dbname, filespec):
        conn = xappy.IndexerConnection(dbname)
        for f in filespec.files():
            self.process_file(f, conn)
        conn.close()
        
    def process_file(self, file_name, conn):
        print "processing file: ", file_name
        with open(file_name) as f:
            doc = xappy.UnprocessedDocument()
            doc.fields.append(xappy.Field('text', f.read()))
            pdoc = conn.process(doc)
            conn.add(pdoc)

def init():
    daemon = Pyro.core.Daemon()
    daemon.useNameServer(Pyro.naming.NameServerLocator().getNS())
    try:
        daemon.connect(Indexer(), "indexer")
        daemon.requestLoop()
    finally:
        daemon.shutdown(True)

if __name__ == "__main__":
    init()
