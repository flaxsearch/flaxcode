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

"""Minimal web app for searching flax.core databases.

FIXME: facets and ranges

"""

import os.path
import web
from mako.template import Template
from mako.lookup import TemplateLookup

import xapian
import flax.core

DBDIR = '/tmp/flaxdemo'

mlookup = TemplateLookup(directories=['templates'])

urls = (
    '^/(\w*)$', 'search',
)

class search:
    def GET(self, dbname):
        web.header('Content-Type','text/html; charset=utf-8', unique=True)

        try:
            if not dbname:
                return 'no database specified'
                
            i = web.input(query='', authfac=[], startrank=0)
            t = mlookup.get_template('search.mako')
                        
            # FIXME - could cache these for efficiency
            db = xapian.Database(os.path.join(DBDIR, dbname))
            fm = flax.core.Fieldmap(db)
            qp = fm.query_parser(db)

            qo = qp.parse_query(i.query)
            if i.authfac:
                qo = fm.FILTER(qo, fm.query('author', i.authfac))
    
            results = fm.search(db, qo, int(i.startrank), 20, 
                                facet_fields=['author'])
    
            return t.render_unicode(query=i.query, results=results,
                authfac=i.authfac).encode('utf-8', 'ignore')

        except xapian.DatabaseOpeningError:
            return 'no database at %s' % os.path.join(DBDIR, dbname)

if __name__ == '__main__':
    app = web.application(urls, globals(), autoreload=True)
    app.run()
