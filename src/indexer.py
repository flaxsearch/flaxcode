from __future__ import with_statement
import collections
import os
import Pyro.core
import Pyro.naming
import filespec
import util
util.setup_sys_path()

import xappy

try:
    import w32com_ifilter
    windows = True
except ImportError:
    windows = False

import simple_text_filter

util.setup_psyco()

class Indexer(Pyro.core.ObjBase):
    
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        self.filter_map = {"Xapian": None,
                           "Text": simple_text_filter.text_filter}
        if windows:
            self.filter_map["IFilter"] =  w32com_ifilter.ifilter_filter

    def do_indexing(self, file_spec, dbname, format_settings):
        print "Indexing xapian db: %s,\n with files from filespec %s\n format settings: %s" % (dbname, file_spec, format_settings)
        self.refresh_xapian_db(dbname, file_spec, format_settings)
        print "Indexing Finished"

    def refresh_xapian_db(self, dbname, filespec, format_settings):
        conn = xappy.IndexerConnection(dbname)
        for f in filespec.files():
            self.process_file(f, conn, format_settings)
        conn.close()


    def find_filter(self, filter_name):
        return self.filter_map[filter_name] if filter_name in self.filter_map else None

    
    def process_file(self, file_name, conn, format_settings):
        print "processing file: ", file_name
        _, ext = os.path.splitext(file_name)
        filter = self.find_filter(format_settings[ext[1:]])
        if filter:
            doc = xappy.UnprocessedDocument()
            for field, content in filter(file_name):
                doc.fields.append(xappy.Field(field, content))
                pdoc = conn.process(doc)
            conn.add(pdoc)
        else:
            print "filter for %s is not valid" % ext

def init():
    daemon = Pyro.core.Daemon()
    ns = Pyro.naming.NameServerLocator().getNS()
    daemon.useNameServer(ns)
    name = 'indexer'
    try:
        ns.unregister(name)
    except Pyro.errors.NamingError:
        pass
    try:
        daemon.connect(Indexer(), name)
        daemon.requestLoop()
    finally:
        daemon.shutdown(True)

if __name__ == "__main__":
    init()
