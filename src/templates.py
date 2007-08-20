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
    
    def dummy_render(self, template):
        pass

    def make_template(self, render_fn, file_name):
        return  HTMLTemplate.Template(render_fn, open(os.path.join(self.template_dir, file_name)).read())

    def create_admin_template(self, file_name,  render_fn = None):
        fn = self.dummy_render if render_fn is None else render_fn
        common_template = self.make_template(fn, "flax.html")
        common_template.banner.raw = self.admin_banner_html
        sub_template = self.make_template(self.dummy_render, file_name)
        common_template.title = sub_template.title
        common_template.main = sub_template.body
        return common_template

    def write_html_file(self, filename, template, *args):
        with open(os.path.join(self.html_dir, filename), 'w') as f:
            f.write(template.render(*args))               


tman = TemplateManager("templates", "html")

index_template = tman.create_admin_template("index.html")

def render_search(template, collections):
    template.main.collections.repeat(do_collection, collections)

def do_collection(node, collection):
    node.col_name.content = collection.name
    node.col_select.atts['value'] = collection.name

admin_search_template = tman.create_admin_template("admin_search.html", render_search)


def render_collections_list(template, collections):
    template.main.collection.repeat(render_collection, collections)

import urllib
def render_collection(node, collection):
    col_url = collection.name+".html"
    node.name.content = collection.name
    node.name.atts['href'] = urllib.quote(col_url)
    node.description.content = collection.description
    node.delete.atts['href'] = urllib.quote(col_url+'/confirm_delete')


collection_list_template = tman.create_admin_template("collections.html", render_collections_list)

def render_collection_detail(template, collection):
    template.title.col_name.content = collection.name
    body = template.main
    body.name.content = collection.name
    body.description.content = collection.description

collection_detail_template = tman.create_admin_template("collection_detail.html", render_collection_detail)

def render_searched_collection(node, col):
    node.content = col.name

def render_search_result(template, query, cols):
    template.main.query.content = query
    template.main.col.repeat(render_searched_collection, cols)

search_result_template = tman.create_admin_template("admin_search_result.html", render_search_result)

import collection
COLLECTIONS = collection.collections()
# Some dummy data for the pages that need collection(s)
foo = COLLECTIONS.new_collection("foo", description = "foo description")
bar = COLLECTIONS.new_collection("bar")

def make_html():
    for d in  (  ("index.html", index_template),
                 ("search.html", admin_search_template, COLLECTIONS), 
                 ("collections.html", collection_list_template,  COLLECTIONS),
                 ("foo.html", collection_detail_template, foo),
                 ("foo_search.html", search_result_template, "aardvark", [foo, bar])):
        tman.write_html_file(*d)
