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

class CollectionPage(resource.Resource):

    addSlash = True

    _template = templates.collection_detail_template
    
    def __init__(self, collection, *args):
        super(CollectionPage, self).__init__(*args)
        self._collection = collection

    def render(self, ctx):
        return http.Response(stream = self._template.render(self._collection))

class CollectionListPage(resource.PostableResource):

    _template = templates.collection_list_template

    def __init__(self, collections, *args):
        self._collections = collections
        super(CollectionListPage, self).__init__(*args)

                       
    def render(self, req):
        if req.method.upper() == "POST" and 'new_name' in req.args:
            name = req.args.get('new_name')[0]
            col = self._collections.new_collection(name)
            return http.RedirectResponse(req.unparseURL(path = req.uri+'/'+name))
        else:
            return http.Response(stream = self._template.render(self._collections))


                                                 
    # TODO: get collections class to act like a dict 
    def locateChild(self, req, segments):
        col_name=segments[0]
        if col_name in self._collections._collections:
            return (CollectionPage(self._collections._collections[col_name]), segments[1:])
        else:
             #404
            return (None, segments)
        
class SearchForm(resource.Resource):

    _template = templates.admin_search_template

    _result_template = templates.search_result_template

    def __init__(self, collections, *args):
        super(SearchForm, self).__init__(*args)
        self._collections = collections

    def render(self, req):
        if 'query' in req.args and 'col' in req.args:
            return http.Response(200, stream = self._result_template.render(req.args['query'][0], req.args['col']))
        else:
            return http.Response(200, stream = self._template.render(self._collections))


class Toplevel(resource.Resource):
    
    addSlash = True
    
    child_static=static.File('static')
    
    child_index = IndexPage()

    child_collections = CollectionListPage(templates.COLLECTIONS)

    child_search = SearchForm(templates.COLLECTIONS)


    def render(self, req):
        return http.RedirectResponse(req.unparseURL(path = 'index'))

site = server.Site(Toplevel())

# Standard twisted application Boilerplate
from twisted.application import service, strports
application = service.Application("flaxserver")
s = strports.service('tcp:8090', channel.HTTPFactory(site))
s.setServiceParent(application)
