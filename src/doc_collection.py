# Copyright (C) 2007 Lemur Consulting Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""Configuration and settings for document collections.

"""
from __future__ import with_statement
__docformat__ = "restructuredtext en"

import sys
import copy
import os
import logging

import util
import filespec
import dbspec
import schedulespec
import setuppaths
import xappy



class DocCollection(filespec.FileSpec, dbspec.DBSpec, schedulespec.ScheduleSpec):
    """Representation of a collection of documents.

    A collection consists of a FileSpec, a DBSpec and a ScheulingSpec, together
    with some properties describing the collection.

    """

    log = logging.getLogger('collections')

    def __init__(self, name, db_dir, *args, **kwargs):
        self.name = name
        self.db_dir = db_dir
        self.indexed = "unknown"
        self.docs = "unknown"
        self.queries = 0
        self.mappings = {}
        self.status = "unindexed"
        self.update(*args, **kwargs)
        self.maybe_make_db()

    def update(self, description="", **kwargs):
        self.description = description
        filespec.FileSpec.update(self, **kwargs)
        dbspec.DBSpec.update(self, **kwargs)
        schedulespec.ScheduleSpec.update(self, **kwargs)
        self.update_mappings(**kwargs)

    def update_mappings(self, path=None, mapping=None, **kwargs):
        
        # This relies on the ordering of the form elements, I'm not
        # sure if it's safe to do so, although it seems to work fine.
        if (path == None or mapping == None):
            return
        self.paths = util.listify(path)
        mappings = util.listify(mapping)
        # be careful with the order here
        pairs = zip(self.paths, mappings)
        self.mappings = dict(filter (lambda (x, y): x !='', pairs))
        self.paths = filter(None, self.paths)
        print self.paths, self.mappings

    def url_for_doc(self, doc_id):
        """ Use the mappings attribute of the collection to give the
        url for the document.  If there is no mapping specified then
        provide a url to serve from Flax if flax_serve is True,
        otherwise just return the empty string.
        """
        #Possibly a file lives below two separate paths, in which case
        #we're just taking the first mapping here. To really address
        #this we'd need to save the path for the source file in the
        #document. It's unlikely to be a big issue tho'.

        path = [ p for p in self.paths if os.path.commonprefix([doc_id, p]) == p]
        if len(path) > 1:
            self.log.warning('Doc: %s has more than one path, using first' % doc_id)
        if len(path) == 0:
            self.log.error('Doc: %s has no path. Maybe the collection needs indexing' % doc_id)
            return "/"
        mapped = self.mappings[path[0]]
        if mapped:
            return mapped+"/"+doc_id[len(path[0]):]
        else:
            return "/"
        
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
