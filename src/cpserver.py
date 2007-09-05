import os

import cherrypy
import templates

class IndexPage(object):

    _template = templates.index_template

    @cherrypy.expose
    def index(self):
        return self._template.render()

class OptionsPage(object):

    _template = templates.options_template

    @cherrypy.expose
    def index(self):
        return self._template.render()

class CollectionPage(object):

    _template = templates.collection_detail_template
    
    def __init__(self, collection, *args):
        self._collection = collection

    def index(self, description = "", paths="", format=[]):

        if cherrypy.request.method == "POST":
            self._collection.description = description
            self._collection.paths = paths.split('\n')
            self._collection.formats = format            

        return self._template.render(self._collection)

class CollectionListPage(object):

     _template = templates.collection_list_template

     def __init__(self, collections):
         self._collections = collections

     @cherrypy.expose
     def default(self, name, *args, **kwargs):
         if name in self._collections:
             return CollectionPage(self._collections[name]).index()
         else:
             return None
     
     @cherrypy.expose
     def index(self, new_name = None, **kwargs):
         if new_name:
             col = self._collections.new_collection(new_name, **kwargs)
             print "PATH: ", cherrypy.request.path_info
             raise cherrypy.HTTPRedirect(cherrypy.request.path_info+new_name)
         else:
             return self._template.render(self._collections.itervalues())

class SearchForm(object):

    def __init__(self, collections, search_template, result_template):
        self._collections = collections
        self._template = search_template
        self._result_template = result_template

    @cherrypy.expose
    def index(self, query = None, col = None):
        if col and query:
            cols = [col] if type(col) is str else col
            return self._result_template.render(query, cols)
        else:
            return self._template.render(self._collections)

         
class Admin(object):

    _index = IndexPage()

    options = OptionsPage()

    collections = CollectionListPage(templates.COLLECTIONS)

    search = SearchForm(templates.COLLECTIONS, templates.admin_search_template, templates.admin_search_result_template)

    @cherrypy.expose
    def index(self):
        return self._index.index()

class TopLevel(object):

    def __init__(self, static_root):
        self.static = cherrypy.tools.staticdir.handler(section = 'static', root = cd, dir = 'static')

    admin = Admin()
    
    search = SearchForm(templates.COLLECTIONS, templates.user_search_template, templates.user_search_result_template)

    #   admin = Admin()

    @cherrypy.expose
    def index(self):
        return self.search.index()
    


if __name__ == "__main__":
    cd = os.path.dirname(os.path.abspath(__file__))
    cherrypy.quickstart(TopLevel(cd), config = "cp.conf")

