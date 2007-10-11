#!/usr/bin/env python
#
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
"""Flax web interface, using the cherrypy webserver.

"""
__docformat__ = "restructuredtext en"

import setuppaths
import os
import cherrypy
import flax
import templates
import persist
import util
util.setup_psyco()

class FlaxResource(object):
    "Abstract class supporting common error handling across all Flax web pages"

    def _only_post(self, message='Only "POST" supported'):
        "utility for raising 405 when we're expecting a post but get something else"
        if cherrypy.request.method != "POST":
            cherrypy.response.headers['Allow'] = "POST"
            raise cherrypy.HTTPError(405, message)

    def _bad_request(self, message="Bad request"):
        "method to signal that data we receive cannot be used"
        raise cherrypy.HTTPError(400, message)

    def _signal_data_changed(self):
        persist.data_changed.set()


class Collections(FlaxResource):
    """
    Controller for web pages dealing with document collections.
    """

    def _bad_collection_name(self, name):
        self._bad_request("%s does not name a collection." % name if name else "No collection name supplied")

    def __init__(self, flax_data, list_template, detail_template, index_server):
        """
        Collections constructor.

        :Parameters:
            - `collections`: The set of document collections.
            - `list_template`: A template for rendering the set of document collections.
            - `detail_template`: A template for rendering a single collection.
        """
        self._flax_data = flax_data
        self._list_template = list_template
        self._detail_template = detail_template
        self._index_server = index_server

    def _redirect_to_view(self, col):
        raise cherrypy.HTTPRedirect('/admin/collections/' + col + '/view' )

    @cherrypy.expose
    def default(self, col_id=None, action=None, **kwargs):
        if col_id and action:
            if action == 'do_indexing':
                return self.do_indexing(col_id, **kwargs)
            elif action == 'update':
                return self.update(col_id, **kwargs)
            elif action == 'view':
                return self.view(col_id, **kwargs)
        elif col_id:
            return self.view(col_id)
        else:
            return self.view()

    def do_indexing(self, col=None, **kwargs):
        """
        (Re)-index a document collection.

        :Parameters:
            - `col`: Names the document collection to be indexed.

        This method forces an immediate indexing of the document
        collection named by the parameter `col`.

        The HTTP method should be POST

        A 400 is returned if either:

        - `col` is ommited; or
        - `col` is present by does not name a collection;
        """

        self._only_post()

        if col and col in self._flax_data.collections:
            self._index_server.do_indexing(self._flax_data.collections[col], self._flax_data.filter_settings)
            self._redirect_to_view(col)
        else:
            self._bad_collection_name(col)

    def update(self, col=None, **kwargs):
        """
        Update the attributes of a document collection.

        :Parameters:
            - `col`: The name of the document collection to be updated.

        Updates the document collection named by `col` with the
        remaining keyword arguments by POSTing.

        Only POST should be used, 405 is returned otherwise.

        If `col` is not supplied or does not name a collection then
        400 is returned.

        """

        self._only_post()

        if col and col in self._flax_data.collections:
            self._flax_data.collections[col].update(**kwargs)
            self._signal_data_changed()
            self._redirect_to_view(col)
        else:
            raise self._bad_collection_name(col)

    @cherrypy.expose
    def new(self, col=None, **kwargs):
        if cherrypy.request.method == "POST":
            if col and col not in self._flax_data.collections:
                self._flax_data.collections.new_collection(col, **kwargs)
                self._signal_data_changed()
                self._redirect_to_view(col)
        else:
            return self._detail_template(None, self._flax_data.formats, self._flax_data.languages)

    @cherrypy.expose
    def view(self, col=None, **kwargs):
        """
        View a document collection.

        :Parameters:
            - `col`: The name of the collection to be viewed.

        Shows the detail for the document collection named by `col`,
        if it exists; otherwise return 404.
        """
        if col:
            if col in self._flax_data.collections:
                return self._detail_template (self._flax_data.collections[col],
                                              self._flax_data.formats,
                                              self._flax_data.languages)
            else:
                raise cherrypy.NotFound()
        else:
            return self._list_template (self._flax_data.collections.itervalues(),
                                        '/admin/collections')

class SearchForm(object):
    """
    A controller for searching document collections and rendering
    the results.
    """

    def __init__(self, collections, search_template, result_template):
        """
        :Parameters:
            - `collections`: the set of document collections to be searched.
            - `search_template`: A template for redering the search form.
            - `result_template`: A template for rendering search results.
        """
        self._collections = collections
        self._template = search_template
        self._result_template = result_template

    def search(self, query = None, col = None, advanced = False, tophit = 0, maxhits = 10):
        """
        Search document collections.

        :Parameters:
            - `query`: the search query
            - `col`: the (list of) collection(s) to be searched.
            - `advanced`: the style of search form.

        If `col` and `query` are provided then use `query` to search
        all the document collections named by `col` and return the
        results. (In this case the value of `advanced` is ignored.)

        Otherwise render a page containing a form to initiate a new
        search. If `advanced` tests true then the form will have more
        structure.
        """
        tophit = int (tophit)
        maxhits = int (maxhits)
        if query:
            cols = [col] if isinstance(col, str) else col
            results = self._collections.search(query, cols, tophit, maxhits)
            return self._result_template (query, self._collections, cols,
                results, tophit, maxhits)
        else:
            return self._template (self._collections, advanced, self._collections._formats)

class Top(FlaxResource):
    """
    A contoller for the default (end-user) web pages.
    """
    def __init__(self, flax_data, search_template, search_result_template):
        """
        Constructor.

        :Parameters:
            - `collections`: collections to be processed.
            - `search_template`: template for the search forms.
            - `search_result_template`: template for rendering search results.
        """

        self._flax_data = flax_data
        self._search = SearchForm(flax_data.collections, search_template, search_result_template)

    @cherrypy.expose
    def index(self):
        return self.search()

    @cherrypy.expose
    def search(self, **kwargs):
        """
        Do a basic (i.e. advanced = False) search. See `SearchForm.search`.
        """
        return self._search.search(advanced=False, **kwargs )

    @cherrypy.expose
    def advanced_search(self, **kwargs):
        """
        Do an advanced (i.e. advanced = True) search. See `SearchForm.search`.
        """
        return self._search.search(advanced=True, **kwargs )

    @cherrypy.expose
    def source(self, col, file_id):
        """
        Serve the source file for the document in document collection
        named by col with file_id id.
        """
        # Quite possibly this is a security hole allowing any
        # documents to be accessed. Need to think carefully about how
        # we actually ensure that we're just serving from the document
        # collections. In any case I guess it makes sense for the
        # process running the web server to have limited read access.
        if col in self._flax_data.collections:
            filename = self._flax_data.collections[col].source_file_from_id(file_id)
            if filename:
                return cherrypy.lib.static.serve_file(filename)
        # fall through we can't find either the collection or the file named by file_id
        raise cherrypy.NotFound()

class Admin(Top):
    """
    A controller for the administration pages.
    """

    def __init__(self, flax_data, search_template, search_result_template, options_template, index_template):
        """
        Constructor.

        :Parameters:
            - `collections`: collections to be processed.
            - `search_template`: template for the search forms.
            - `search_result_template`: template for rendering search results.
            - `options_template`: template for the global options page.
            - `index_template`: template for the index page.
        """
        self._options_template = options_template
        self._index_template = index_template
        super(Admin, self).__init__(flax_data, search_template, search_result_template)

    @cherrypy.expose
    def options(self, **kwargs):
        """
        Render the options template.
        """
        if cherrypy.request.method == "POST":

            for arg in ("db_dir", "flax_dir"):
                if arg in kwargs:
                    setattr(self._flax_data, arg, kwargs[arg])

            self._flax_data.log_settings = kwargs

        return self._options_template (self._flax_data)

    @cherrypy.expose
    def index(self):
        """
        Render the index template.
        """
        return self._index_template ()


def start_web_server(flax_data, index_server):
    """
    Run Flax web server.
    """
    collections = Collections(flax_data,
                              templates.collection_list_render,
                              templates.collection_detail_render,
                              index_server)

    admin = Admin(flax_data,
                  templates.admin_search_render,
                  templates.admin_search_result_render,
                  templates.options_render,
                  templates.index_render)

    top = Top(flax_data, templates.user_search_render, templates.user_search_result_render)

    cherrypy.Application.root=top
    cherrypy.Application.root.admin = admin
    cherrypy.Application.root.admin.collections = collections
    cherrypy.quickstart(top, config = 'cp.conf')

def startup():
    import optparse
    import logclient
    import scheduler
    import sys
    sys.path.append('indexserver')
    import indexer
    import processing
    op = optparse.OptionParser()
    op.add_option('-i', '--input-file', dest='input_file', help = "Flax input data file (default is flax.flx)", default = 'flax.flx')
    op.add_option('-o', '--output-file', dest='output_file', help= "Flax output data file (default is flax.flx)", default = 'flax.flx')
    (options, args) = op.parse_args()
    flax.options = persist.read_flax(options.input_file)
    try:
        webserver_logconfio = processing.Pipe()
        index_server = indexer.IndexServer()
        logclient.LogConfPub('flaxlog.conf', [webserver_logconfio[0], index_server.logconf_input])
        logclient.LogListener(webserver_logconfio[1]).start()
        logclient.LogConf().update_log_config()
        scheduler.ScheduleIndexing(index_server).start()
        persist.DataSaver(options.output_file).start()
        start_web_server(flax.options, index_server)
        print "Flax web server shutting down..."
    finally:
        persist.store_flax(options.output_file, flax.options)

if __name__ == "__main__":
    startup()
