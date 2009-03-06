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


    def update(self, language='', stopwords='', **kwargs):
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

    def dbpath(self):
        """This method must return a path to the database.

        """
        raise NotImplementedError, "Subclasses must implement dbpath"

    def maybe_make_db(self):
        dbpath = self.dbpath()
        if not os.path.exists(dbpath):
            os.makedirs(dbpath)

            conn = xappy.IndexerConnection(dbpath)

            add_internal_field_actions(conn, self.stopwords, self.language)

            free_text_options = { 'stop' : self.stopwords,
                                  'spell': True,
                                  'language' : self.language }

            conn.add_field_action('title', xappy.FieldActions.INDEX_FREETEXT,
                                  **free_text_options)
            conn.add_field_action('title', xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action('content', xappy.FieldActions.INDEX_FREETEXT,
                                  **free_text_options)
            conn.add_field_action('content', xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action("description", xappy.FieldActions.INDEX_FREETEXT,
                                  **free_text_options)
            conn.add_field_action("description", xappy.FieldActions.STORE_CONTENT)

            conn.add_field_action("keyword", xappy.FieldActions.INDEX_FREETEXT,
                                  **free_text_options)
            conn.add_field_action("keyword", xappy.FieldActions.STORE_CONTENT)

            conn.close()


def internal_fields():
    """Get a list of the fields which are for internal use only.

    Such fields must not be returned by filters.

    """
    return ('filename', 'uri', 'nametext', 'mtime', 'size', 'collection', 'filetype',)

def add_internal_field_actions(conn, stopwords, language):
    """Add field actions for the internal fields.

    The fields for which actions are set up here MUST be the same as those
    returned by internal_fields().

    """
    free_text_options = {
        'stop' : stopwords,
        'spell': True,
        'language' : language,
    }

    # The source file (on the local system) that corresponds to this file.
    conn.add_field_action("filename", xappy.FieldActions.INDEX_EXACT)
    conn.add_field_action("filename", xappy.FieldActions.STORE_CONTENT)

    # The URI that a document corresponds to.
    # (Not currently used, but we define it now so that we won't need
    # to reorganise the fields later to add it.  Having it defined
    # but not used should have virtually no cost.)
    conn.add_field_action("uri", xappy.FieldActions.INDEX_EXACT)
    conn.add_field_action("uri", xappy.FieldActions.STORE_CONTENT)

    # Text extracted from the filepath.
    # This is used to allow the filename to have some influence on the
    # search results.
    conn.add_field_action("nametext", xappy.FieldActions.INDEX_FREETEXT,
                          **free_text_options)

    # The time that a document was last modified.
    # This is stored in seconds since the epoch (ie, time.gmtime(0))
    conn.add_field_action("mtime", xappy.FieldActions.INDEX_EXACT)
    conn.add_field_action("mtime", xappy.FieldActions.STORE_CONTENT)

    # The size is just used for display.
    conn.add_field_action("size", xappy.FieldActions.STORE_CONTENT)

    # The collection that a document belongs to.
    # We may be able to replace this by a "virtual" field at some
    # point, because it will be the same for all documents in a given
    # collection.
    conn.add_field_action("collection", xappy.FieldActions.INDEX_EXACT)
    conn.add_field_action("collection", xappy.FieldActions.STORE_CONTENT)

    # filetype is just the extention to support searching by "format"
    # (at some point we'll add a mimetype field as well, or instead).
    conn.add_field_action('filetype', xappy.FieldActions.INDEX_EXACT)
    conn.add_field_action('filetype', xappy.FieldActions.STORE_CONTENT)
            
