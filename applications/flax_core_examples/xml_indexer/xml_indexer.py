# Copyright (C) 2010 Lemur Consulting Ltd
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

"""Minimal example of a flax.core indexing application, using lxml to
index XML.

"""

from __future__ import with_statement

import os, os.path
import time
import logging

from lxml import etree
import xapian
import flax.core

LANGUAGE = 'en'

class Indexer(object):
    """FIXME
    
    """
    def __init__(self, db_path, actions_path, root_tag):
        self.db_path = db_path
        self.actions = flax.core.actions.parse_actions(actions_path)
        self.root_tag = root_tag
        
        try:
            self.db = xapian.WritableDatabase(db_path, xapian.DB_OPEN)
            self.fieldmap = flax.core.Fieldmap(self.db)
        except xapian.DatabaseOpeningError:
            # create the database and fieldmap
            self.db = xapian.WritableDatabase(db_path, xapian.DB_CREATE)
            
            # create a fieldmap from the actions and save it
            self.fieldmap = flax.core.Fieldmap(language=LANGUAGE)
            for act in self.actions:
                self.fieldmap.setfield(act.fieldname, act.action.isfilter)
                
            self.fieldmap.save(self.db)
            self.db.flush()
            
    def index_file(self, path):
        with open(path) as f:
            for event, element in etree.iterparse(f):
                if element.tag == self.root_tag:
                    self.index_element(element)

        self.db.flush()
        print 'done'

    def index_element(self, element):
        """Index an XML element as one xapian document.
        
        """
        doc = self.fieldmap.document()
        print 'indexing', element.tag
        for act in self.actions:
            for item in element.xpath(act.external_key):
                if not isinstance(item, basestring):
                    raise Exception, \
                        'xpath expression "%s" does not evaluate to a string' % field.xpath
                act.action(act.fieldname, item, doc)

        doc.set_data(etree.tostring(element))
        self.fieldmap.add_document(self.db, doc)

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 5:
        print "usage: python xml_indexer.py <db path> <xml file> <actions> <root tag>"
    else:
        indexer = Indexer(sys.argv[1], sys.argv[3], sys.argv[4])
        indexer.index_file(sys.argv[2])
    