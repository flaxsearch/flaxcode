# $Id$
from __future__ import with_statement
import sys
import copy
import os
import Pyro.core

import filespec
import dbspec
import schedulespec
import util
util.setup_sys_path()
import xappy

class DocCollection(filespec.FileSpec, dbspec.DBSpec, schedulespec.ScheduleSpec):
    """
    Flax Document Collection.

    A collection is a FileSpec, an IndexingSpec and a ScheulingSpec.

    In addition it has properties describing the collection.
    """

    def __init__(self, name, db_dir, *args, **kwargs):
        self.name = name
        self.db_dir = db_dir
        self.indexed = "unknown"
        self.docs = "unknown"
        self.queries = 0
        self.status = "unindexed"
        self.update(*args, **kwargs)
        self.maybe_make_db()
        

    def update(self, description="", **kwargs):
        self.description = description
        filespec.FileSpec.update(self, **kwargs)
        dbspec.DBSpec.update(self, **kwargs)
        schedulespec.ScheduleSpec.update(self, **kwargs)
                
    def do_indexing(self, filter_settings):
        indexer = Pyro.core.getProxyForURI("PYRONAME://indexer")
#        indexer._setOneway("do_indexing")
        indexer.do_indexing(self, self.dbname(), filter_settings)
        

    def dbname(self):
        return os.path.join(self.db_dir, self.name+'.db')

    def source_file_from_id(self, file_id):
        "return the source file name given a document id."
        try:
            # all this does at the moment is check that this file
            # has been indexed as part of this document collection.
            conn = xappy.SearchConnection(self.dbname())
            conn.get_document(file_id)
            conn.close()
            return file_id
        except KeyError:
            return None
