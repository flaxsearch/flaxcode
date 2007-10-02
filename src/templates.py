# $Id$
""" HTMLTemplates for Flax and rendering thereof.
"""

from __future__ import with_statement
import os
import urllib
import HTMLTemplate

import util

class TemplateManager(object):
    """
    Facilities for making HTMLTemplates for Flax with preconfigured
    banner sections from files on disk.
    """

    def __init__(self, template_dir, html_dir, admin_banner_file="admin_banner.html", user_banner_file="user_banner.html"):
        """
        Constructor

        :Parameters:
           - `template_dir`: The directory for loading template files.
           - `html_dir`: The directory for writing html files.
           - `user_banner_file`: The name of the file to use as the banner for user templates.
           - `admin_banner_file`: The name of the file to use as the banner for admin templates.
        """
        self.template_dir = template_dir
        self.html_dir = html_dir
        self.admin_banner_file = admin_banner_file
        self.user_banner_file = user_banner_file
        self._cache = {}
    
    def dummy_render(self, template):
        """
        A renderer that does nothing.
        """
        pass

    def make_template(self, render_fn, file_name):
        """
        Make an HTMLTemplate from `file_name` in `template_dir` using `render_fn`.
        
        """
        fpath = os.path.join (self.template_dir, file_name)
        mtime = os.path.getmtime(fpath)
        key = (file_name, render_fn)
        try:
            cached = self._cache[key]
            if cached[1] == mtime:
                return cached[0]

        except KeyError:
            pass
            
        t = HTMLTemplate.Template(render_fn, open(fpath).read())
        self._cache[key] = (t, mtime)
        return t

    def create_template(self, file_name,  banner, render_fn = None):
        fn = self.dummy_render if render_fn is None else render_fn
        common_template = self.make_template(fn, "flax.html")
        common_template.banner.raw = banner
        sub_template = self.make_template(self.dummy_render, file_name)
        if hasattr(sub_template, 'title'):
            common_template.title = sub_template.title
        common_template.main = sub_template.body
        if hasattr(sub_template, 'heads'):
            common_template.heads = sub_template.heads
        else:
            common_template.heads.raw = ''
        return common_template

    def create_admin_template(self, file_name, render_fn = None):
        """
        Make an administrator template.
        """
        admin_banner_html = self.make_template (self.dummy_render, self.admin_banner_file).render()
        return self.create_template(file_name, admin_banner_html, render_fn)

    def create_user_template(self, file_name, render_fn = None):
        """
        Make a user template.
        """
        user_banner_html = self.make_template (self.dummy_render, self.user_banner_file).render()
        return self.create_template(file_name, user_banner_html, render_fn)

    def write_html_file(self, filename, template, *args):
        """
        Render a template as html to a file.
        """
        with open(os.path.join(self.html_dir, filename), 'w') as f:
            f.write(template.render(*args))        

##### Options Template #####

def render_options(template, flax_data):

    template.main.db_dir.atts["value"] = flax_data.db_dir
    template.main.flax_dir.atts["value"] = flax_data.flax_dir

    def fill_log_events(node, event):
        # the empty string can be used to name the root logger
        node.event_label.content = event if event else "default"

        def fill_input(inp, level):
            inp.atts["name"] = event
            inp.atts["value"] = level
            inp.content = level[0]
            if flax_data.log_settings[event] == level:
                inp.atts['checked'] = 'on'
            
        node.event_radio.repeat(fill_input, flax_data.log_levels) 
                
    template.main.collection_events.repeat(fill_log_events, sorted(flax_data.log_settings))

    def fill_meanings(span, level):
        span.raw = '<strong>%s</strong>%s' % (level[0], level[1:])

    template.main.level_meaning.repeat(fill_meanings, flax_data.log_levels)

    def fill_formats(node, fmt):
        
        def fill_filters(node, filter_name):
            node.atts["value"] = filter_name
            node.content = filter_name
            if filter_name == flax_data.filter_settings[fmt]:
               node.atts["selected"]="selected"
 
        node.format_label.content = fmt
        node.format_select.atts['name'] = fmt
        node.format_select.filter.repeat(fill_filters, flax_data.filters)

    template.main.format_filters.repeat(fill_formats, flax_data.formats)

##### Search Templates #####

def render_search(template, collections, advanced=False, formats=[]):
    template.main.collections.repeat (render_search_collection, collections.itervalues())
    if advanced:
        template.main.advanced_holder=_advanced_search_options().body
        def fill_format(node, format):
            node.format_label.content = format
            node.format_checkbox.atts['value'] = format
            node.format_checkbox.atts['checked'] = 'on' 
            
        template.main.advanced_holder.formats.repeat(fill_format, formats)
    else:
        template.main.advanced_holder.raw = ""


def render_search_collection (node, collection, selected=None):
    node.col_name.content = collection.name
    node.col_select.atts['value'] = collection.name
    if selected and collection.name in selected:
        node.col_select.atts['checked'] = 'true'

##### Collection List Template #####

def render_collections_list(template, collections, base_url):
    template.main.add_form.atts['action'] = base_url + '/add/'
    template.main.add_form.collection.repeat(render_collection, collections, base_url)

def render_collection(node, collection, base_url):
    col_url = base_url + '/' + collection.name + '/view'
    node.name.content = collection.name
    node.name.atts['href'] = urllib.quote(col_url)
    node.description.content = collection.description
    node.indexed.content = str(collection.indexed)
    node.doc_count.content = str(collection.docs)
    node.query_count.content = str(collection.queries)
    node.status.content = str(collection.status)

    node.delete.atts['href'] = urllib.quote(col_url+'/confirm_delete')

###### Collection Detail Template ######

# This actually sucks a bit, really we want to make all the checkbox
# and associated labels nodes at initialization time, and then just
# set the checked attributes at render time, but the public api for
# HTMLTemplate doesn't really support that - the repeat thing builds
# new structure, really we want a way of iterating over the already
# built items to set the checked value.

def render_collection_detail(template, collection, formats, languages):
    template.title.col_name.content = collection.name
    body = template.main
    body.name.content = collection.name

    body.description.atts['value'] = collection.description
    body.paths.content = '/n'.join(collection.paths) if isinstance(collection.paths, list) else collection.paths
 
    def fill_format(node, format):
        node.format_label.content = format
        node.format_checkbox.atts['value'] = format
        if format in collection.formats:
            node.format_checkbox.atts['checked'] = 'on' 

    body.formats.repeat(fill_format, formats)

    for prop in ("earliest", "latest"):
        val = getattr(collection, prop)
        if val:
            getattr(body, prop).atts["value"] = val.strftime(collection.strptime_format)

    for prop in ("oldest", "youngest"):
        val = getattr(collection, prop)
        if val:
            getattr(body, prop).atts["value"] = util.render_timedelta(val)

    def fill_languages(node, val):
        node.atts["value"] = val[0]
        node.content = val[1]
        if val[0] == collection.language:
            node.atts['selected'] = "selected"

    body.language_option.repeat(fill_languages, languages)
    body.stopwords.atts["value"] = " ".join(collection.stopwords)


    def render_spec(spec):
        sep = ', '
        if isinstance(spec, str):
            return spec
        return sep.join(map(str, spec))

    body.mins.atts['value'] = render_spec(collection.mins)
    body.hours.atts['value'] = render_spec(collection.hours)
    body.monthdays.atts['value'] = render_spec(collection.monthdays)
    body.weekdays.atts['value'] = render_spec(collection.weekdays)
    body.months.atts['value'] = render_spec(collection.months)

    
###### Search Result Templates ######

def render_searched_collection(node, col):
    node.content = col

def render_search_result (template, query, collections, selcols, results, tophit, maxhits):
    # collections is the list of available collections
    # selcols is a list of selected collections
    
    def fill_results(node, res):
        # res is xapian results object
        if 'filename' in res.data and 'collection' in res.data:
            filename = res.data['filename'][0]
            collection = res.data['collection'][0]
            url = '/source?col=%s&file_id=%s' % (collection, filename)
            node.res_link.atts['href']=url
            node.res_link.content = '%d. %s' % (res.rank + 1, filename)
            
        if 'content' in res.data:
            node.res_content.raw = res.summarise('content', hl=('<strong>','</strong>'))

    template.main.query.atts['value'] = query
    template.main.collections.repeat (render_search_collection, collections.itervalues(), selcols)

    if results.startrank < results.endrank:
        template.main.results.repeat(fill_results, results)
        template.main.info.content = '%s to %s of %s%d matching documents' % (
            results.startrank + 1, results.endrank, 
            '' if results.estimate_is_exact else 'about ', 
            results.matches_human_readable_estimate) 
    
        q = urllib.quote_plus (query)
        if results.startrank:
            template.main.nav.first_page.atts['href'] = '?query=%s' % q
            template.main.nav.prev_page.atts['href'] = '?query=%s&tophit=%d' % (q, 
                results.startrank - maxhits)
        else:
            template.main.nav.first_page.atts['class'] = 'link_disabled'
            template.main.nav.prev_page.atts['class'] = 'link_disabled'

        if results.more_matches:
            template.main.nav.next_page.atts['href'] = '?query=%s&tophit=%d' % (q, 
                results.startrank + maxhits)
        else:
            template.main.nav.next_page.atts['class'] = 'link_disabled'

    else:
        # no search results
        template.main.info.content = 'No matching documents found'
        template.main.nav.omit()
        

_tman = TemplateManager ("templates", "html")

#: Template admin index pages.
def index_render (*args):
    return _tman.create_admin_template("index.html").render (*args)

#: Template for global options page
def options_render (*args):
    return _tman.create_admin_template("options.html", render_options).render (*args)

#: template for administrator search pages.
def admin_search_render (*args):
    return _tman.create_admin_template("search.html", render_search).render (*args)

#: template for user search pages.
def user_search_render (*args):
    return _tman.create_user_template("search.html", render_search).render (*args)

#: template for collections listing
def collection_list_render (*args):
    return _tman.create_admin_template("collections.html", render_collections_list).render (*args)

#: template for viewing a collection.
def collection_detail_render (*args):
    return _tman.create_admin_template("collection_detail.html", render_collection_detail).render (*args)

#: administrator template for viewing search results.
def admin_search_result_render (*args):
    return _tman.create_admin_template("search_result.html", render_search_result).render (*args)

#: user template for viewing search results.
def user_search_result_render (*args):
    return _tman.create_user_template("search_result.html", render_search_result).render (*args)

# used internally
def _advanced_search_options ():
    return _tman.make_template(_tman.dummy_render, "advanced_search.html")


