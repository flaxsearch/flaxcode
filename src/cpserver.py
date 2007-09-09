#$Id:$

# Copyright (C) 2007 Lemur Consulting Ltd

# This software may be used and distributed according to the terms
# of the GNU General Public License, incorporated herein by reference.
"""
Flax web server.
"""
__docformat__ = "restructuredtext en"
import os
import cherrypy
import routes
import templates

class Collections(object):
    """
    Controller for web pages dealing with document collections.
    """

    def __init__(self, collections, list_template, detail_template):
         self._collections = collections
         self._list_template = list_template
         self._detail_template = detail_template

    def do_indexing(self, col=None, **kwargs):
        if cherrypy.request.method == "POST" and col and col in self._collections:
            self._collections[col].make_xapian_db()
            self.redirect_to_show(col)
        else:
            raise cherrypy.NotFound() 
         
    def update(self, col=None, **kwargs):
        if col and col in self._collections:
            self._collections[col].update(**kwargs)
            self.redirect_to_show(col)
        else:
            raise cherrypy.NotFound() 
     
    def add(self, col = None, **kwargs):
        if col:
            self._collections.new_collection(col, **kwargs)
            self.redirect_to_show(col)
        else:
            raise cherrypy.NotFound()

    def redirect_to_show(self, col):
        raise cherrypy.HTTPRedirect('/admin/collections/' + col + '/view' )

    def view(self, col=None, **kwargs):
        if col:
            if col in self._collections:
                return self._detail_template.render(self._collections[col])
            else:
                raise cherrypy.NotFound()
        else:
            return self._list_template.render(self._collections.itervalues(), routes.url_for('/admin/collections'))

class SearchForm(object):

    def __init__(self, collections, search_template, result_template):
        self._collections = collections
        self._template = search_template
        self._result_template = result_template

    def search(self, query = None, col = None, advanced = False):
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

         
class Admin(object):

    def __init__(self, collections, search_template, search_result_template, options_template, index_template):
        self._collections = collections
        self._options_template = options_template
        self._index_template = index_template
        self._admin_search = SearchForm(collections,
                                        search_template,
                                        search_result_template)

    def options(self):
        return self._options_template.render()

    def search(self, **kwargs):
        return self._admin_search.search(advanced=False, **kwargs )

    def advanced_search(self, **kwargs):
        return self._admin_search.search(advanced=True, **kwargs )

    def index(self):
        return self._index_template.render()

class Top(object):

    def __init__(self, collections, search_template, search_result_template):
        self._collections = collections
        self._user_search = SearchForm(collections, search_template, search_result_template)

    def search(self, **kwargs):
        return self._user_search.search(advanced=False, **kwargs)

    def advanced_search(self, **kwargs):
        return self._user_search.search(advanced=True,  **kwargs )


def setup_routes(top_controller, admin_contoller, collections_controller):

    d = cherrypy.dispatch.RoutesDispatcher()
    d.connect('top', '/', controller = top_controller, action='search')
    d.connect('user_search', '/search', controller = top_controller, action='search')

    d.connect('collections_add', 'admin/collections/add', controller = collections_controller, action='add')
    d.connect('collections', '/admin/collections/:col/:action', controller = collections_controller, action='view')
    d.connect('collections_default', '/admin/collections/', controller = collections_controller, action='view')

    d.connect('admin', '/admin/:action', action='index', controller=admin_contoller )

    return d


if __name__ == "__main__":
    cd = os.path.dirname(os.path.abspath(__file__))
    collections = templates.COLLECTIONS

    top = Top(collections, templates.user_search_template, templates.user_search_result_template)

    admin = Admin(collections,
                  templates.admin_search_template,
                  templates.admin_search_result_template,
                  templates.options_template,
                  templates.index_template)
    
    collections = Collections(collections,
                              templates.collection_list_template,
                              templates.collection_detail_template)

    d = setup_routes(top, admin, collections)
    
    cherrypy.config.update('cp.conf')
    cherrypy.quickstart(None, config = { '/': { 'request.dispatch': d},
                                         '/static': {'tools.staticdir.on': True,
                                                     'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
                                                     'tools.staticdir.dir': 'static'}})
