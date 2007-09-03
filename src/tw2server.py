""" twisted.web2 server.
    invoke with:  twistd -ny tw2server.py
"""

from twisted.web2 import resource, http, static, server, channel

import templates

class IndexPage(resource.Resource):

    addSlash = True

    _template = templates.index_template

    def render(self, ctx):
        return http.Response(stream = self._template.render())

class OptionsPage(resource.Resource):

    addSlash = True

    _template = templates.options_template

    def render(self, ctx):
        return http.Response(stream = self._template.render())

class CollectionPage(resource.PostableResource):

    addSlash = True

    _template = templates.collection_detail_template
    
    def __init__(self, collection, *args):
        super(CollectionPage, self).__init__(*args)
        self._collection = collection

    def render(self, req):

        if req.method.upper() == "POST":
            if 'description' in req.args:
                self._collection.description = req.args.get('description')[0]
            if 'paths' in req.args:
                self._collection.paths = req.args.get('paths')[0].split('\n')
            if 'format' in req.args:
                self._collection.formats = req.args.get('format')

        return http.Response(stream = self._template.render(self._collection))

class CollectionListPage(resource.PostableResource):

    _template = templates.collection_list_template

    def __init__(self, collections, *args):
        self._collections = collections
        super(CollectionListPage, self).__init__(*args)

    def render(self, req):
        if req.method.upper() == "POST" and 'new_name' in req.args:
            name = req.args.get('new_name')[0]
            col = self._collections.new_collection(name, **req.args)
            return http.RedirectResponse(req.unparseURL(path = req.uri+'/'+name))
        else:
            return http.Response(stream = self._template.render(self._collections.itervalues()))
                                                 
    def locateChild(self, req, segments):
        col_name=segments[0]
        if col_name in self._collections:
            return (CollectionPage(self._collections[col_name]), segments[1:])
        else:
             #404
            return (None, segments)
        
class SearchForm(resource.Resource):

    def __init__(self, collections, search_template, result_template, *args):
        super(SearchForm, self).__init__(*args)
        self._collections = collections
        self._template = search_template
        self._result_template = result_template

    def render(self, req):
        if 'query' in req.args and 'col' in req.args:
            return http.Response(200, stream = self._result_template.render(req.args['query'][0], req.args['col']))
        else:
            return http.Response(200, stream = self._template.render(self._collections))

class Admin(resource.Resource):

    addSlash = True

    child_index = IndexPage()

    child_options = OptionsPage()
    
    child_collections = CollectionListPage(templates.COLLECTIONS)

    child_search = SearchForm(templates.COLLECTIONS, templates.admin_search_template, templates.admin_search_result_template)

    def render(self, req):
        return http.RedirectResponse(req.unparseURL(path = req.uri+'index'))

class Toplevel(resource.Resource):
    
    addSlash = True
    
    child_search = SearchForm(templates.COLLECTIONS, templates.user_search_template, templates.user_search_result_template)

    child_admin = Admin()

    child_static=static.File('static')

    def render(self, req):
        return http.RedirectResponse(req.unparseURL(path = req.uri+'search'))

site = server.Site(Toplevel())

# Standard twisted application Boilerplate
from twisted.application import service, strports
application = service.Application("flaxserver")
s = strports.service('tcp:8090', channel.HTTPFactory(site))
s.setServiceParent(application)
