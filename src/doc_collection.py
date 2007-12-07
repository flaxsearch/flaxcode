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

import copy
import logging
import os
import sys
import urllib

import setuppaths
import xappy

import dbspec
import filespec
import flax
import flaxpaths
import schedulespec
import util

class DocCollection(filespec.FileSpec, dbspec.DBSpec, schedulespec.ScheduleSpec):
    """Representation of a collection of documents.

    A collection consists of a FileSpec, a DBSpec and a ScheulingSpec, together
    with some properties describing the collection.

    """

    log = logging.getLogger('collections')

    def __init__(self, name, *args, **kwargs):
        # deleted is set to True when the database is marked as deleted - it
        # will then shortly actually be deleted.
        self.deleted = False

        self.name = name
        self.mappings = {}
        self.update(*args, **kwargs)
        self.indexing_due = False
        self.indexing_held = False
        self.file_count = 0
        self.error_count = 0
        self.maybe_make_db()

    def update(self, description="", **kwargs):
        self.description = description
        if 'formats' in kwargs and kwargs['formats'] and 'html' in kwargs['formats']:
            kwargs['formats'] = util.listify(kwargs['formats'])
            kwargs['formats'].append('htm')
        filespec.FileSpec.update(self, **kwargs)
        dbspec.DBSpec.update(self, **kwargs)
        schedulespec.ScheduleSpec.update(self, **kwargs)
        self._update_mappings(**kwargs)

    def _update_mappings(self, path=None, mapping=None, **kwargs):
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

    def ready_to_be_indexed(self):
        """Return True iff this collection is ready to be indexed.

        """
        return self.indexing_due and not self.indexing_held and not self.deleted

    def url_for_doc(self, doc_id):
        """Calculate the URL to display for a document.
        
        Uses the mappings attribute of the collection to give the url for the
        document.  If there is no mapping specified then just return the empty
        string.

        If a file lives below more than one path which is mapped, the longest
        such path is used (since it will be the most specific).

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
        if mapped == 'FLAX':
            return ('/source/%s/%s' % (self.name, urllib.quote(doc_id))) 
        elif mapped:
            return mapped + "/" + doc_id[len(path[0]):].replace('\\', '/')
        else:
            return ""

    def search_conn(self):
        return flax.options.collections.get_search_connection(self.name)

    @property
    def document_count(self):
        return self.search_conn().get_doccount()

    def dbpath(self):
        return os.path.join(flaxpaths.paths.dbs_dir, self.name + '.db')

    def source_file_from_id(self, doc_id):
        "return the source file name given a document id."
        conn = self.search_conn()
        try:
            doc = conn.get_document(doc_id)
        except KeyError:
            return None
        conn.close()
        return doc_id

