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
