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

import os
import re
import setuppaths
import cherrypy
import cplogger
import templates
import persist
import util
import logging

import platform
_is_windows = platform.system() == 'Windows'
if _is_windows:
    import win32api
    import string

from previewgen import WSGIPreviewGen

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
    """Controller for web pages dealing with document collections.

    """
    _valid_colname_re = re.compile (r'[\w \.\-_]{1,100}$')

    def _bad_collection_name(self, name):
        """Return an error page describing a problem with a collection name.

        """
        self._bad_request("%s does not name a collection." % name if name else "No collection name supplied")

    def __init__(self, flax_data, list_template, detail_template, index_server):
        """Collections constructor.

        :Parameters:
            - `flax_data`: The flax configuration and status data.
            - `list_template`: A template for rendering the set of document
              collections.
            - `detail_template`: A template for rendering a single collection.
            - `index_server`: The index server - used to control and monitor
              indexing progress.

        """
        self._flax_data = flax_data
        self._list_template = list_template
        self._detail_template = detail_template
        self._index_server = index_server

    def _redirect_to_view(self, col=None):
        """Redirect to a view page.

        If `col` is specified, redirects to the view page for that collection -
        otherwise redirects to the view page which lists all the collections.

        """
        if col:
            raise cherrypy.HTTPRedirect('/admin/collections/' + col + '/view' )
        else:
            raise cherrypy.HTTPRedirect('/admin/collections/')

    @cherrypy.expose
    def default(self, col_id=None, action=None, **kwargs):
        """Default handler.
        
        Calls the appropriate sub handler based on the action parameter.

        """
        if col_id and action:
            if action == 'toggle_due':
                return self.toggle_due_or_held(col_id, **kwargs)
            elif action == 'delete':
                return self.delete(col_id, **kwargs)
            elif action == 'toggle_held':
                return self.toggle_due_or_held(col_id, held=True, **kwargs)
            elif action == 'update':
                return self.update(col_id, **kwargs)
            elif action == 'view':
                return self.view(col_id, **kwargs)
        elif col_id:
            return self.view(col_id)
        else:
            return self.view()

    def toggle_due_or_held(self, col=None, held=False, **kwargs):
        """Set or clears one of the flags controlling collection indexing.

        :Parameters:
            - `col`: Names the document collection to be indexed.
            - `held`: If True set the held flag, otherwise the due flag.

        The HTTP method should be POST

        A 400 is returned if either:

        - `col` is omitted; or
        - `col` is present by does not name a collection;

        """
        self._only_post()

        if col and col in self._flax_data.collections:
            self._index_server.toggle_due_or_held(self._flax_data.collections[col], held)
            return self._redirect_to_view()
        else:
            self._bad_collection_name(col)

    def delete(self, col=None, **kwargs):
        """Delete a document collection.

        :Parameters:
            - `col`: The name of the document collection to be deleted.

        """
        self._only_post()

        if col in self._flax_data.collections:
            self._index_server.stop_indexing(self._flax_data.collections[col])
            self._flax_data.collections.remove_collection(col)
            return self._redirect_to_view()

    def update(self, col=None, **kwargs):
        """Update the attributes of a document collection.

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
            collection = self._flax_data.collections[col]
            collection.update(**kwargs)
            self._signal_data_changed()
            self._redirect_to_view()
        else:
            raise self._bad_collection_name(col)

    @cherrypy.expose
    def new(self, col=None, **kwargs):
        """Create a new document collection.

        """
        if cherrypy.request.method == "POST":
            if not self._valid_colname_re.match(col):
                self._bad_request("The collection name is not valid")            
            elif col:
                error = self._flax_data.collections.new_collection(col, **kwargs)
                if error is not None:
                    self._bad_request(error)
                self._signal_data_changed()
                self._redirect_to_view()
            else:
                self._bad_request("A collection name must be provided for new collections")

        else:
            return self._detail_template(None, self._flax_data.formats, self._flax_data.languages)        

    @cherrypy.expose
    def view(self, col=None, **kwargs):
        """View a document collection.

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
                                        '/admin/collections',
                                        self._index_server)

    @cherrypy.expose
    def json (self, col=None, **kwargs):
        """Return collection information in JSON format.
        
        """
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        # prevent IE caching
        cherrypy.response.headers['Expires'] = 'Mon, 26 Jul 1997 05:00:00 GMT'

        if col:
            return '"NOT IMPLEMENTED"'
        else:
            # order by name
            cols = [(c.name, c) for c in self._flax_data.collections.itervalues()]
            cols.sort()
            cols = [c[1] for c in cols]
            ret = []
            for c in cols:
                status, fc, ec = self._index_server.indexing_info (c)
                ret.append ({"name":        c.name,
                             "status":      int(status),
                             "index_due":   int(c.indexing_due),
                             "index_held":  int(c.indexing_held),
                             "doc_count":   c.document_count,
                             "file_count":  fc,
                             "error_count": ec })
            return repr (ret)


class SearchForm(object):
    """Controller for searching document collections and rendering
    the results.

    """

    def __init__(self, flax_data, search_template, advanced_template):
        """Constructor.

        :Parameters:
            - `flax_data`: The flax options object.
            - `search_template`: Template for rendering the standard search form (and results).
            - `advanced_template`: Template for rendering advanced search form (and results).

        """
        self._flax_data = flax_data
        self._template = search_template
        self._advanced_template = advanced_template

    def search(self, query=None, col=None, col_id=None, doc_id=None,
               advanced=False, format=None, exact=None, exclusions=None,
               tophit=0, maxhits=10, sort_by=None,
               filenameq=None):
        """Search document collections.

        :Parameters:
            - `query`: the search query
            - `col`: the (list of) collection(s) to be searched.
            - `doc_id`: A document to generate a search query.
            - `advanced`: the style of search form.

        One of `query` or (`col_id` and `doc_id`) should be provided

        If `col` and `query` are provided then use `query` to search
        all the document collections named by `col` and return the
        results. (In this case the value of `advanced` is ignored.)

        Otherwise render a page containing a form to initiate a new
        search. If `advanced` tests true then the form will have more
        structure.

        """
        assert not (query and doc_id)
        template = self._advanced_template if advanced else self._template

        if col:
            cols = util.listify(col)
        else:
            cols = []

        if format:
            formats = util.listify(format)
        else:
            formats = []

        tophit = int (tophit)
        maxhits = int (maxhits)
        if ((query or exact or exclusions or format or filenameq)
            or (col_id and doc_id)):
            if 'html' in formats:
                formats.append('htm')
            results = self._flax_data.collections.search(
                query, col_id=col_id, doc_id=doc_id, cols=cols, format=format,
                exact=exact, exclusions=exclusions, tophit=tophit,
                maxhits=maxhits, sort_by=sort_by, filenameq=filenameq)
            return template(self._flax_data.collections, results, cols,
                            self._flax_data.formats, formats, sort_by,
                            filenameq)
        else:
            return template(self._flax_data.collections, None, cols,
                            self._flax_data.formats, formats, sort_by,
                            filenameq)

class Top(FlaxResource):
    """
    A contoller for the default (end-user) web pages.
    """
    def __init__(self, flax_data, search_template, advanced_template,
                 about_template):
        """
        Constructor.

        :Parameters:
            - `flax_data`: flax data to supply to templates.
            - `search_template`: Template for rendering the standard search form (and results).
            - `advanced_template`: Template for rendering advanced search form (and results).
            - `about_template`: template for the about page.

        """
        self._flax_data = flax_data
        self._search = SearchForm(flax_data,
                                  search_template, advanced_template)
        self._about_template = about_template

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect('advanced_search'
                                    if self._flax_data.advanced_as_default
                                    else 'search')

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
    def source(self, col, *unused):
        """Serve a source file for a document.

        The document collection is specified in the first part of the path,
        followed by the filename of the document.

        """
        # Read the path from the unprocessed path_info string, rather than the
        # value supplied to us in the function arguments by cherrypy. This
        # avoids problems with repeated slashes being removed.
        pathbits = cherrypy.request.path_info.split('/')
        if len(pathbits) < 4:
            raise cherrypy.NotFound()

        # Build doc_id by joining the pieces with os.path.sep.
        doc_id = os.path.sep.join(pathbits[3:])

        # Quite possibly this is a security hole allowing any
        # documents to be accessed. Need to think carefully about how
        # we actually ensure that we're just serving from the document
        # collections. In any case I guess it makes sense for the
        # process running the web server to have limited read access.
        if col in self._flax_data.collections:
            if self._flax_data.collections[col].path_is_within_collection(doc_id):
                return cherrypy.lib.static.serve_file(doc_id)

        # We can't find either the collection or the file named by file_id
        raise cherrypy.NotFound()

    @cherrypy.expose
    def about(self):
        """Display the "About" page.

        """
        return self._about_template()


class Admin(Top):
    """A controller for the administration pages.

    """

    def __init__(self,
                 flax_data,
                 search_template,
                 advanced_template,
                 about_template,
                 options_template,
                 filebrowser_template):
        """Constructor.

        :Parameters:
            - `flax_data`: flax data to supply to templates.
            - `search_template`: template for the search forms.
            - `advanced_template`: template for the advanced search.
            - `about_template`: template for the about page.
            - `options_template`: template for the global options page.

        """
        self._options_template = options_template
        self._filebrowser_template = filebrowser_template
        super(Admin, self).__init__(flax_data,
                                    search_template, advanced_template,
                                    about_template)

    @cherrypy.expose
    def options(self, advanced_as_default=None, **kwargs):
        """Render the options template.

        """

        if cherrypy.request.method == "POST":
            if self._flax_data.advanced_as_default != advanced_as_default:
                self._flax_data.advanced_as_default = advanced_as_default
                self._signal_data_changed()
            self._flax_data.log_settings = kwargs
            # Redirect to prevent reloads redoing the POST.
            raise cherrypy.HTTPRedirect('options')
        return self._options_template(self._flax_data)

    @cherrypy.expose
    def index(self):
        """Currently no use for home page, so redirect to collections list.

        """
        raise cherrypy.HTTPRedirect('collections')

    @cherrypy.expose
    def filebrowser(self):
        """Return a file browser.

        This is under Admin so that normal users cannot access it.

        """
        return self._filebrowser_template()

    @cherrypy.expose
    def listfiles(self, fpath=''):
        """List files in fpath (assuming it is a directory).

        Returns a JSON list:

        [[filepath, filename, is-dir, is-readable], ...]

        """
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        # prevent IE caching
        cherrypy.response.headers['Expires'] = 'Mon, 26 Jul 1997 05:00:00 GMT'

        if fpath:
            ret = []
            try:
                for f in os.listdir(fpath):
                    fp = os.path.join(fpath, f).replace('\\', '/')
                    canread = int(os.access(fp, os.R_OK))
                    if os.path.isdir(fp):
                        ret.append ([fp, f + os.path.sep, 1, canread])
                    else:
                        ret.append ([fp, f, 0, canread])

            # in the case of errors, log them but return an empty list to the browser
            except Exception, e:
                logging.getLogger('collection').error('error file-listing %s: %s' %
                    (fpath, e))

            return repr(ret)

        else:
            # special case - return list of filesystem roots
            # filter out floppy drives
            if _is_windows:
                drives = win32api.GetLogicalDriveStrings()
                drives = string.splitfields(drives,'\000')
                drives = [[d.replace('\\', '/'), d, 1, 1] for d in drives
                          if d and d not in ('A:\\', 'B:\\')]
                return repr(drives)
            else:
                return "[['/', '/', 1, 1]]"


def start_web_server(flax_data, index_server, conf_path, templates_path, blocking=True):
    """Start the web server.

    """
    renderer = templates.Renderer(templates_path)
    collections = Collections(flax_data,
                              renderer.collection_list_render,
                              renderer.collection_detail_render,
                              index_server)

    admin = Admin(flax_data,
                  renderer.admin_search_render,
                  renderer.admin_advanced_search_render,
                  renderer.admin_about_render,
                  renderer.options_render,
                  renderer.filebrowser_render)

    top = Top(flax_data,
              renderer.user_search_render,
              renderer.user_advanced_search_render,
              renderer.user_about_render)

    admin.collections = collections
    top.admin = admin

    # this has to come before cherrypy makes any application objects
    # if cp logging is to be properly integrated with the rest of flax
    # logging.
    cherrypy.log.logger_root = 'webserver'

    # HACK - customise the generic error template
    cherrypy._cperror._HTTPErrorTemplate = open(
        os.path.join(templates_path, 'cp_http_error.html')).read()

    cherrypy.config.update(conf_path)
    cherrypy.tree.mount(top, '/', config=conf_path)
    cherrypy.tree.graft(WSGIPreviewGen(),
                        '/make_preview')
    
    if _is_windows:
        
        # this is necessary because we make COM calls withing the
        # threads that cp creates. At the time of writing this is only
        # done from Top.make_preview.

        import pythoncom

        def InitializeCOM(threadIndex):
            pythoncom.CoInitializeEx(pythoncom.COINIT_MULTITHREADED)

        def UninitializeCOM(threadIndex):
            pythoncom.CoUninitialize()

        
        # subscription protocol varies amongst cherrypy versions - if
        # this errors google "cherrypy engine subscribe" - for 3.1 or
        # newer the following 2 lines should work:      
        cherrypy.engine.subscribe('start_thread', InitializeCOM)
        cherrypy.engine.subscribe('stop_thread', UninitializeCOM)

        # On older versions the following two lines should work:
        #cherrypy.engine.on_start_thread_list.append(InitializeCOM)
        #cherrypy.engine.on_stop_thread_list.append(UninitializeCOM)
        

    cherrypy.engine.start()
    if blocking:
        cherrypy.engine.block()

def stop_web_server():
    """Stop the flax web server.

    """
    #calling this blocks sometimes, whereas simply terminating the
    #process without calling it seems to work fine, so we don't call
    #it - see: http://code.google.com/p/flaxcode/issues/detail?id=153
    #cherrypy.server.stop()
    pass
