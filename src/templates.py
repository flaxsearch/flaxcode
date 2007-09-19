# $Id$
""" HTMLTemplates for Flax and rendering thereof.
"""

from __future__ import with_statement
import os
import urllib
import HTMLTemplate

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
        self.admin_banner_html = self.make_template(self.dummy_render, admin_banner_file).render()
        self.user_banner_html = self.make_template(self.dummy_render, user_banner_file).render()
    
    def dummy_render(self, template):
        """
        A renderer that does nothing.
        """
        pass

    def make_template(self, render_fn, file_name):
        """
        Make an HTMLTemplate from `file_name` in `template_dir` using `render_fn`.
        
        """
        return  HTMLTemplate.Template(render_fn, open(os.path.join(self.template_dir, file_name)).read())

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
        return self.create_template(file_name, self.admin_banner_html, render_fn)

    def create_user_template(self, file_name, render_fn = None):
        """
        Make a user template.
        """
        return self.create_template(file_name, self.user_banner_html, render_fn)

    def write_html_file(self, filename, template, *args):
        """
        Render a template as html to a file.
        """
        with open(os.path.join(self.html_dir, filename), 'w') as f:
            f.write(template.render(*args))        


tman = TemplateManager("templates", "html")

##### Index Template #####

#: Template admin index pages.
index_template = tman.create_admin_template("index.html")

##### Options Template #####


def render_options(template, flax_data):

    template.main.db_dir.atts["value"] = flax_data.db_dir
    template.main.flax_dir.atts["value"] = flax_data.flax_dir

    def fill_log_events(node, event):
        node.event_label.content = event

        def fill_input(inp, level):
            inp.atts["name"] = event
            inp.atts["value"] = level
            inp.content = level[0]
            if flax_data.log_settings[event] == level:
                inp.atts['checked'] = 'on'
            
        node.event_radio.repeat(fill_input, flax_data.log_levels) 
                
    template.main.collection_events.repeat(fill_log_events, flax_data.log_events)

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

#: Template for global options page
options_template = tman.create_admin_template("options.html", render_options)

##### Search Templates #####

_advanced_search_options = tman.make_template(tman.dummy_render, "advanced_search.html")

def render_search(template, collections, advanced=False, formats=[]):
    template.main.collections.repeat(do_collection, collections.itervalues())
    if advanced:
        template.main.advanced_holder=_advanced_search_options.body
        def fill_format(node, format):
            node.format_label.content = format
            node.format_checkbox.atts['value'] = format
            node.format_checkbox.atts['checked'] = 'on' 
            
        template.main.advanced_holder.formats.repeat(fill_format, formats)
    else:
        template.main.advanced_holder.raw = ""


def do_collection(node, collection):
    node.col_name.content = collection.name
    node.col_select.atts['value'] = collection.name

#: template for administrator search pages.
admin_search_template = tman.create_admin_template("search.html", render_search)

#: template for user search pages.
user_search_template = tman.create_user_template("search.html", render_search)

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

#: template for collections listing
collection_list_template = tman.create_admin_template("collections.html", render_collections_list)

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
    body.paths.content = '/n'.join(collection.paths) if type(collection.paths) is list else collection.paths

    def fill_format(node, format):
        node.format_label.content = format
        node.format_checkbox.atts['value'] = format
        if format in collection.formats:
            node.format_checkbox.atts['checked'] = 'on' 

    body.formats.repeat(fill_format, formats)

    def fill_languages(node, val):
        node.atts["value"] = val[0]
        node.content = val[1]
        if val[0] == collection.language:
            node.atts['selected'] = "selected"

    body.language_option.repeat(fill_languages, languages)
    body.stopwords.atts["value"] = " ".join(collection.stopwords)
    
#: template for viewing a collection.
collection_detail_template = tman.create_admin_template("collection_detail.html", render_collection_detail)


###### Search Result Templates ######

def render_searched_collection(node, col):
    node.content = col

def render_search_result(template, query, cols, result=None):
    template.main.query.content = query
    template.main.col.repeat(render_searched_collection, cols)
    if result:
        template.main.results.content = result

#: administrator template for viewing search results.
admin_search_result_template = tman.create_admin_template("search_result.html", render_search_result)

#: user template for viewing search results.
user_search_result_template = tman.create_user_template("search_result.html", render_search_result)

def make_html():
    for d in  (  ("index.html", index_template),
                 ("search.html", admin_search_template, COLLECTIONS), 
                 ("collections.html", collection_list_template,  COLLECTIONS),
                 ("foo.html", collection_detail_template, foo),
                 ("foo_search.html", admin_search_template, "aardvark", [foo, bar])):
        tman.write_html_file(*d)

if __name__ == "__main__":
   # make_html()
   pass
