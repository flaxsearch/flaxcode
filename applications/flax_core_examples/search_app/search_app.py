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

"""Minimal example web app for searching flax.core databases, demonstrating
searching, filters, facets and ranges.

To run this app, you will need 

    - xapian, with Python bindings ( http://xapian.org/ )
    - flax.core ( http://code.google.com/p/flaxcode/source/checkout )
    - web.py framework ( http://webpy.org/ )
    - mako templates ( http://www.makotemplates.org/ )

You will also need one or more xapian databases created with a flax.core
indexer (such as applications/flax_core_examples/xml_indexer in the flaxcode
repository).

Run the search app from the command line:

    $ python search_app.py

And point a browser at http://localhost:8080/ to choose and search a database.

"""

import os.path
import web
from mako.template import Template
from mako.lookup import TemplateLookup

import xapian
import flax.core

# change this to the directory that contains the flax.core databases
DBDIR = '/tmp/flaxdemo'

mlookup = TemplateLookup(directories=['templates'])

urls = (
    '^/$', 'list',
    '^/(.*)/search$', 'search',
)

class list:
    def GET(self):
        web.header('Content-Type','text/html; charset=utf-8', unique=True)
        dbs = [x for x in os.listdir(DBDIR) if x[0] != '.' and 
               os.path.isdir(os.path.join(DBDIR, x))]
       
        t = mlookup.get_template('list.mako')
        return t.render_unicode(
            dbs=dbs).encode('utf-8', 'ignore')

class search:
    def GET(self, dbname):
        web.header('Content-Type','text/html; charset=utf-8', unique=True)

        try:
            if not dbname:
                return 'no database specified'
            
            # get query string parameters
            i = web.input(query='', authfac=[], startrank=0, 
                          yearfrom='', yearto='')
            
            # open the xapian Database and get the flax.core fieldmap object
            # FIXME - could cache these for efficiency
            db = xapian.Database(os.path.join(DBDIR, dbname))
            fieldmap = flax.core.Fieldmap(db)
            
            # get a query parser and parse the query
            queryparser = fieldmap.query_parser(db)
            query = queryparser.parse_query(i.query)
            
            # add authors filter, if supplied
            if i.authfac:
                query = fieldmap.FILTER(query, fieldmap.query('author', i.authfac))
    
            # add year range filter, if supplied
            if i.yearfrom or i.yearto:
                yf = int(i.yearfrom) if i.yearfrom else 0
                yt = int(i.yearto) if i.yearto else 3000
                query = fieldmap.FILTER(query, fieldmap.range_query('published', yf, yt))

            # do the search, collecting facets for the author field
            results = fieldmap.search(db, query, int(i.startrank), 20, 
                                      facet_fields=['author'])

            # render and return the page
            t = mlookup.get_template('search.mako')
            return t.render_unicode(
                query=i.query, 
                results=results,
                authfac=i.authfac, 
                yearfrom=i.yearfrom, 
                yearto=i.yearto,
                ).encode('utf-8', 'ignore')

        except xapian.DatabaseOpeningError:
            return 'no database at %s' % os.path.join(DBDIR, dbname)

if __name__ == '__main__':
    app = web.application(urls, globals(), autoreload=True)
    app.run()
