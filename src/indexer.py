from __future__ import with_statement
import itertools
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
    """ A class that performs indexing on demand by remote invocation.
    """
    
    def __init__(self):
        Pyro.core.ObjBase.__init__(self)
        self._filter_map = {"Xapian": None,
                            "Text": simple_text_filter.text_filter}
        if windows:
            self._filter_map["IFilter"] =  w32com_ifilter.ifilter_filter

    def do_indexing(self, file_spec, dbname, filter_settings):
        """
        Index the database dbname with files given by file_spec
        using filters given by filter_settings.
        """
        print "Indexing xapian db: %s,\n with files from filespec %s\n filter settings: %s" % (dbname, file_spec, filter_settings)
        conn = xappy.IndexerConnection(dbname)
        for f in file_spec.files():
            self._process_file(f, conn, filter_settings)
        conn.close()
        print "Indexing Finished"

    def _find_filter(self, filter_name):
        return self._filter_map[filter_name] if filter_name in self._filter_map else None
    
    def _process_file(self, file_name, conn, filter_settings):
        print "processing file: ", file_name
        _, ext = os.path.splitext(file_name)
        filter = self._find_filter(filter_settings[ext[1:]])
        if filter:
            conn.add(xappy.UnprocessedDocument(fields = itertools.starmap(xappy.Field, filter(file_name))))
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
