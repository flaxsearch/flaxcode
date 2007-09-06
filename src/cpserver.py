import os
import cherrypy
import routes
import templates

class Collections(object):

     _template = templates.collection_list_template
     _detail_template = templates.collection_detail_template

     def __init__(self, collections):
         self._collections = collections

     def default(self, name):
         if name in self._collections:
             return CollectionPage(self._collections[name])
         else:
             return None

     def show(self, id=None):
         if id in self._collections:
             return self._detail_template.render(self._collections[id])
         else:
             raise cherrypy.NotFound(path) 

     def do_indexing(self, id=None, **kwargs):
         if cherrypy.request.method == "POST" and id and self._collections[id]:
             print "calling make_xapian_db"
             self._collections[id].make_xapian_db()
             return self._detail_template.render(self._collections[id])
         else:
             raise cherrypy.NotFound(path) 
         
     def update(self, id=None, **kwargs):
         if id and id in self._collections:
             self._collections[id].update(**kwargs)
             return self._detail_template.render(self._collections[id])
         else:
             raise cherrypy.NotFound(path) 
     
     def add(self, new_name, **kwargs):
         if new_name:
             col = self._collections.new_collection(new_name, **kwargs)
             raise cherrypy.HTTPRedirect('/'.join(cherrypy.request.path_info.split('/')[:-2]+[new_name, 'show']))
         else:
             raise cherrypy.NotFound(path)

     def index(self, *args, **kwargs):
         return self._template.render(self._collections.itervalues(), routes.url_for('/admin/collections'))

class SearchForm(object):

    def __init__(self, collections, search_template, result_template):
        self._collections = collections
        self._template = search_template
        self._result_template = result_template

    def search(self, query = None, col = None):
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
            return self._template.render(self._collections)

         
class Admin(object):

    def __init__(self, collections):
        self.admin_search = SearchForm(collections,
                                       templates.admin_search_template,
                                       templates.admin_search_result_template)
    def options(self):
        return templates.options_template.render()

    def search(self, *args, **kwargs):
        return self.admin_search.search(*args, **kwargs)

    def index(self):
        return templates.index_template.render()


class Top(object):

    def __init__(self):
        self.user_search = SearchForm(templates.COLLECTIONS, templates.user_search_template, templates.user_search_result_template)

    def search(self, *args, **kwargs):
        return self.user_search.search(*args, **kwargs)



def setup_routes():
    d = cherrypy.dispatch.RoutesDispatcher()
    top = Top()
    admin = Admin(templates.COLLECTIONS)
    collections = Collections(templates.COLLECTIONS)

    d.connect('top', '/', controller = top, action='search')
    d.connect('user_search', '/search', controller = top, action='search')

    d.connect('collections', '/admin/collections/add', controller = collections, action='add', conditions=dict(method=['POST']))
    d.connect('collection', '/admin/collections/:(id)/:action', controller = collections)
     
    d.connect('admin', '/admin/:action/', controller = admin)
    
    return d


if __name__ == "__main__":
    cd = os.path.dirname(os.path.abspath(__file__))
    d = setup_routes()
    cherrypy.config.update('cp.conf')
    cherrypy.quickstart(None, config = { '/': { 'request.dispatch': d},
                                         '/static': {'tools.staticdir.on': True,
                                                     'tools.staticdir.root': os.path.dirname(os.path.abspath(__file__)),
                                                     'tools.staticdir.dir': 'static'}})
