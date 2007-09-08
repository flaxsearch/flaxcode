# $Id$
""" HTMLTemplates for Flax and rendering thereof

    This code is just to do enough to get some templates rendered for viewing in a web browser.

    Some of this can maybe be used later, but that's not particularly the intention, 
    we just want to get the look and feel of the main web pages right.
"""

from __future__ import with_statement
import HTMLTemplate
import os

class TemplateManager(object):

    def __init__(self, template_dir, html_dir):
        self.template_dir = template_dir
        self.html_dir = html_dir
        self.admin_banner_html = self.make_template(self.dummy_render, "admin_banner.html").render()
        self.user_banner_html = self.make_template(self.dummy_render, "user_banner.html").render()
    
    def dummy_render(self, template):
        pass

    def make_template(self, render_fn, file_name):
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
        return self.create_template(file_name, self.admin_banner_html, render_fn)

    def create_user_template(self, file_name, render_fn = None):
        return self.create_template(file_name, self.user_banner_html, render_fn)

    def write_html_file(self, filename, template, *args):
        with open(os.path.join(self.html_dir, filename), 'w') as f:
            f.write(template.render(*args))               


tman = TemplateManager("templates", "html")

##### Index Template #####

index_template = tman.create_admin_template("index.html")

##### Options Template #####

# these need to come from elsewhere:
_log_events = ("Create Collection",
               "Modify Collection",
               "Delete Collection",
               "Index Collection",
               "Filter file",
               "Add to doc",
               "Remove from doc",
               "Add to db",
               "Remove from db",
               "Run search",
               "Format results")

_event_levels = ("None", "Critical", "Error", "Warning", "Info", "Debug", "All")

_default_level = _event_levels[3]

def render_options(template, events=_log_events, levels=_event_levels):

    def fill_log_events(node, event):
        node.event_label.content = event

        def fill_input(inp, level):
            inp.atts["name"] = event
            inp.atts["value"] = level
            inp.content = level[0]
            if level == _default_level:
                inp.atts['checked'] = 'on'
            
        node.event_radio.repeat(fill_input, _event_levels) 

    template.main.collection_events.repeat(fill_log_events, events)

    def fill_meanings(span, level):
        span.raw = '<strong>%s</strong>%s' % (level[0], level[1:])

    template.main.level_meaning.repeat(fill_meanings, levels)

options_template = tman.create_admin_template("options.html", render_options)


##### Search Templates #####

advanced_search_options = tman.make_template(tman.dummy_render, "advanced_search.html")

def render_search(template, collections, advanced=False, formats=[]):
    template.main.collections.repeat(do_collection, collections.itervalues())
    if advanced:
        template.main.advanced_holder=advanced_search_options.body
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

admin_search_template = tman.create_admin_template("search.html", render_search)
user_search_template = tman.create_user_template("search.html", render_search)

##### Collection List Template #####

def render_collections_list(template, collections, base_url):
    template.main.add_form.atts['action'] = base_url + '/add/'
    template.main.add_form.collection.repeat(render_collection, collections, base_url)

import urllib
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

collection_list_template = tman.create_admin_template("collections.html", render_collections_list)

###### Collection Detail Template ######


# this should come from elsewhere
_formats = ("txt", "doc", "html")

# This actually sucks a bit, really we want to make all the checkbox
# and associated labels nodes at initialization time, and then just
# set the checked attributes at render time, but the public api for
# HTMLTemplate doesn't really support that - the repeat thing builds
# new structure, really we want a way of iterating over the already
# built items to set the checked value.

def render_collection_detail(template, collection):
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

    body.formats.repeat(fill_format, _formats)
    

collection_detail_template = tman.create_admin_template("collection_detail.html", render_collection_detail)


###### Search Result Templates ######

def render_searched_collection(node, col):
    node.content = col

def render_search_result(template, query, cols, result=None):
    template.main.query.content = query
    template.main.col.repeat(render_searched_collection, cols)
    if result:
        template.main.results.content = result

admin_search_result_template = tman.create_admin_template("search_result.html", render_search_result)
user_search_result_template = tman.create_user_template("search_result.html", render_search_result)

# Some dummy data for the pages that need collection(s)
import datetime
import collection
import random
COLLECTIONS = collection.collections()
foo = COLLECTIONS.new_collection("foo", 
                                 description = "foo description",
                                 paths = ["/usr/share/doc"],
                                 formats = ["txt", "doc"],
                                 indexed = datetime.date.today(),
                                 queries = random.randrange(100000),
                                 docs = random.randrange(100000),
                                 status = 0)

bar = COLLECTIONS.new_collection("bar")

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
