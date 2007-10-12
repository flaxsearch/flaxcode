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
"""Database configuration and field specification.

"""
__docformat__ = "restructuredtext en"

import types
import os

import setuppaths
import xappy

class DBSpec(object):
    """This class describes the configuration for a database.

    The configuration specifies how databases should be created, and provides a
    method for creating the database with the appropriate configuration.

    This class should be subclassed by an object describing a source of data
    to be indexed.

    """

    _default_stopwords = ['i', 'a', 'an', 'and', 'the']


    def update(self, language="en", stopwords=_default_stopwords, **kwargs):
        """Update the configuration:

         - `language` specifies the language to be used for a database.
           Currently, this applies to all free-text fields.
         - `stopwords` specifies the stopwords to be used for a database.

        """
        self.language = language

        if isinstance(stopwords, types.StringTypes):
            stopwords = stopwords.split(" ")
        self.stopwords = list(stopwords)

        self.maybe_make_db()

    def dbname(self):
        """This method must return a path to the database.

        FIXME - rename to dbpath, dbname implies that only the basename needs
        to be returned.

        """
        raise NotImplementedError, "Subclasses must implement dbname"


    def maybe_make_db(self):
        dbname = self.dbname()
        if not os.path.exists(dbname):
            os.makedirs(dbname)

            conn = xappy.IndexerConnection(dbname)

            free_text_options = { 'stop' : self.stopwords,
                                  'spell': True,
                                  'language' : self.language }

            conn.add_field_action("filename", xappy.FieldActions.INDEX_EXACT)
            conn.add_field_action("filename", xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action("basename", xappy.FieldActions.INDEX_FREETEXT, **free_text_options)
            conn.add_field_action("basename", xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action("collection", xappy.FieldActions.INDEX_EXACT)
            conn.add_field_action("collection", xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action("keyword", xappy.FieldActions.INDEX_FREETEXT, **free_text_options)
            conn.add_field_action("keyword", xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action("description", xappy.FieldActions.INDEX_FREETEXT, **free_text_options)
            conn.add_field_action("description", xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action("mtime", xappy.FieldActions.INDEX_EXACT)
            conn.add_field_action("mtime", xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action("size", xappy.FieldActions.INDEX_EXACT)
            conn.add_field_action("size", xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action('content', xappy.FieldActions.INDEX_FREETEXT, **free_text_options)
            conn.add_field_action('content', xappy.FieldActions.STORE_CONTENT)
            conn.close()
