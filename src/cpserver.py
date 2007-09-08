import os
import cherrypy
import routes
import templates

class Collections(object):

     _template = templates.collection_list_template
     _detail_template = templates.collection_detail_template

     def __init__(self, collections):
         self._collections = collections

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
          print kwargs
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
               return self._template.render(self._collections.itervalues(), routes.url_for('/admin/collections'))

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

     def __init__(self, collections):
          self._collections = collections
          self.admin_search = SearchForm(collections,
                                         templates.admin_search_template,
                                         templates.admin_search_result_template)
     def options(self):
          return templates.options_template.render()

     def search(self, **kwargs):
          return self.admin_search.search(advanced=False, **kwargs )

     def advanced_search(self, **kwargs):
          return self.admin_search.search(advanced=True, **kwargs )

     def index(self):
          return templates.index_template.render()


class Top(object):

     def __init__(self, collections):
          self._collections = collections
          self.user_search = SearchForm(collections,
                                        templates.user_search_template,
                                        templates.user_search_result_template)

     def search(self, **kwargs):
          return self.user_search.search(advanced=False, **kwargs)

     def advanced_search(self, **kwargs):
          return self.user_search.search(advanced=True,  **kwargs )


def setup_routes(collections):
    d = cherrypy.dispatch.RoutesDispatcher()
    top = Top(collections)
    admin = Admin(collections)
    collections = Collections(collections)

    d.connect('top', '/', controller = top, action='search')
    d.connect('user_search', '/search', controller = top, action='search')

    d.connect('collections_add', 'admin/collections/add', controller = collections, action='add')
    d.connect('collections', '/admin/collections/:col/:action', controller = collections, action='view')
    d.connect('collections_default', '/admin/collections/', controller = collections, action='view')

    d.connect('admin', '/admin/:action', action='index', controller=admin )

    return d


if __name__ == "__main__":
    cd = os.path.dirname(os.path.abspath(__file__))
    d = setup_routes(templates.COLLECTIONS)
    cherrypy.config.update('cp.conf')
    cherrypy.quickstart(None, config = { '/': { 'request.dispatch': d},
                                         '/static': {'tools.staticdir.on': True,
                                                     'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
                                                     'tools.staticdir.dir': 'static'}})
