#$Id : foo $

# Copyright (C) 2007 Lemur Consulting Ltd

# This software may be used and distributed according to the terms
# of the GNU General Public License, incorporated herein by reference.
"""
Flax web server.
"""
import os
import cherrypy
import routes

import flax
import templates


class Collections(object):
    """
    Controller for web pages dealing with document collections.
    """

    def __init__(self, collections, list_template, detail_template):
        """
        Collections constructor.
        
        :Parameters:
            - `collections`: The set of document collections.
            - `list_template`: A template for rendering the set of document collections.
            - `detail_template`: A template for rendering a single collection.
        """
        self._collections = collections
        self._list_template = list_template
        self._detail_template = detail_template

    def _redirect_to_view(self, col):
        raise cherrypy.HTTPRedirect('/admin/collections/' + col + '/view' )

    def do_indexing(self, col=None, **kwargs):
        """
        (Re)-index a document collection.
        
        :Parameters:
            - `col`: Names the document collection to be indexed.

        This method forces an immediate indexing of the document
        collection named by the parameter `col` when the HTTP method
        is POST. A 404 is returned if either:
        
        - `col` is ommited; or
        - `col` is present by does not name a collection;
        - or if the HTTP method is not POST.
        """

        if cherrypy.request.method == "POST" and col and col in self._collections:
#            self._collections[col].make_xapian_db()
            self._collections[col].do_indexing()
            self._redirect_to_view(col)
        else:
            raise cherrypy.NotFound() 
         
    def update(self, col=None, **kwargs):
        """
        Update the attributes of a document collection.

        :Parameters:
            - `col`: The name of the document collection to be updated.

        Updates the document collection named by `col` with the
        remaining keyword arguments by POSTing. If `col` is not
        supplied, does not name a collection or the HTTP method is not
        POST then 404 is returned.

        """
        if  cherrypy.request.method == "POST" and col and col in self._collections:
            self._collections[col].update(**kwargs)
            self._redirect_to_view(col)
        else:
            raise cherrypy.NotFound() 
     
    def add(self, col = None, **kwargs):
        """
        Create a new document collection.

        :Parameters:
            - `col`: The name for the new collection.

        Creates a new collection named `col`. The remaining keywords
        args are used to update the new collection.

        If col is not provided or there is already a collection named
        `col` or the HTTP method is not POST then a 404 is returned.
        """
        if cherrypy.request.method == "POST" and col and not col in self._collections:
            self._collections.new_collection(col, **kwargs)
            self._redirect_to_view(col)
        else:
            raise cherrypy.NotFound()

    def view(self, col=None, **kwargs):
        """
        View a document collection.

        :Parameters:
            - `col`: The name of the collection to be viewed.

        Shows the detail for the document collection named by `col`,
        if it exists; otherwise return 404.
        """
        if col:
            if col in self._collections:
                return self._detail_template.render(self._collections[col])
            else:
                raise cherrypy.NotFound()
        else:
            return self._list_template.render(self._collections.itervalues(),
                                              routes.url_for('/admin/collections'))

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

    def search(self, query = None, col = None, advanced = False):
        """
        Search document collections.

        :Parameters:
            - `query`: the search query
            - `col`: the (list of) collection(s) to be searched.
            - `advanced`: the style of search form.

        If `col` and `query` are provided then use `query` to search all
        the document collections named by `col` and return the
        results. (In this case the value of `advanced` is ignored.)

        Otherwise render a page containing a form to initiate a new
        search. If `advanced` tests true then the form will have more
        structure.
        """
        if col and query:
            cols = [col] if type(col) is str else col
            col_results = (self._collections[c].search(query) for c in cols)
            text = ""
            for res in col_results:
                for r in res:
                    if 'text' in r.data:
                        text+= r.data['text'][0]
            return self._result_template.render(query, cols, text)
        else:
            return self._template.render(self._collections, advanced, self._collections._formats)



class Top(object):
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

    def search(self, **kwargs):
        """
        Do a basic (i.e. advanced = False) search. See `SearchForm.search`.
        """
        return self._search.search(advanced=False, **kwargs )

    def advanced_search(self, **kwargs):
        """
        Do an advanced (i.e. advanced = True) search. See `SearchForm.search`.
        """
        return self._search.search(advanced=True, **kwargs )

         
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

    def options(self, **kwargs):
        """
        Render the options template.
        """
        if cherrypy.request.method == "POST":

            print kwargs
            for arg in ("db_dir", "flax_dir"):
                if arg in kwargs:
                    setattr(self._flax_data, arg, kwargs[arg])

            for log_event in self._flax_data.log_events:
                if log_event in kwargs:
                    self._flax_data.log_settings[log_event] = kwargs[log_event]

            for format in self._flax_data.formats:
                if format in kwargs:
                    self._flax_data.filter_settings[format] = kwargs[format]

        return self._options_template.render(self._flax_data)

    def index(self):
        """
        Render the index template.
        """
        return self._index_template.render()


def setup_routes(top_controller, admin_contoller, collections_controller):
    """
    Define the mapping from urls to objects/methods for the CherryPy routes dispatcher.
    """

    d = cherrypy.dispatch.RoutesDispatcher()
    d.connect('top', '/', controller = top_controller, action='search')
    d.connect('user_search', '/search', controller = top_controller, action='search')

    d.connect('collections_add', 'admin/collections/add', controller = collections_controller, action='add')
    d.connect('collections', '/admin/collections/:col/:action', controller = collections_controller, action='view')
    d.connect('collections_default', '/admin/collections/', controller = collections_controller, action='view')

    d.connect('admin', '/admin/:action', action='index', controller=admin_contoller )

    return d


def main():
    """
    Run Flax web server.
    """
    cd = os.path.dirname(os.path.abspath(__file__))

    flax_data = flax.options

    top = Top(flax_data, templates.user_search_template, templates.user_search_result_template)

    admin = Admin(flax_data,
                  templates.admin_search_template,
                  templates.admin_search_result_template,
                  templates.options_template,
                  templates.index_template)
    
    collections = Collections(flax_data.collections,
                              templates.collection_list_template,
                              templates.collection_detail_template)

    d = setup_routes(top, admin, collections)
    
    cherrypy.config.update('cp.conf')
    cherrypy.quickstart(None, config = { '/': { 'request.dispatch': d},
                                         '/static': {'tools.staticdir.on': True,
                                                     'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
                                                     'tools.staticdir.dir': 'static'}})


if __name__ == "__main__":
    main()


