# $Id$
""" HTMLTemplates for Flax and rendering thereof.
"""

from __future__ import with_statement
import os
import urllib
import datetime
import time
import types
import functools

import HTMLTemplate

import uistrings
import util

class TemplateManager(object):
    """
    Facilities for making HTMLTemplates for Flax with preconfigured
    banner sections from files on disk.
    """

    def __init__(self, template_dir,
                 admin_banner_file="admin_banner.html",
                 user_banner_file="user_banner.html"):
        """
        Constructor

        :Parameters:
           - `template_dir`: The directory for loading template files.
           - `user_banner_file`: The name of the file to use as the banner for user templates.
           - `admin_banner_file`: The name of the file to use as the banner for admin templates.
        """
        self.template_dir = template_dir
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

    def create_template(self, file_name, banner, render_fn=None, real_id=None):
        fn = render_fn if render_fn else self.dummy_render
        common_template = self.make_template(fn, "flax.html")
        sub_template = self.make_template(self.dummy_render, file_name)
        if real_id:
            sub_template.body.atts['id']=real_id
        try:
            banner.banner.atts['id'] = 'banner_'+sub_template.body.atts['id']
        except (KeyError, AttributeError):
            pass
        common_template.banner.raw = banner.render()

        if hasattr(sub_template, 'title'):
            common_template.title = sub_template.title
        common_template.main = sub_template.body
        if hasattr(sub_template, 'heads'):
            common_template.heads = sub_template.heads
        else:
            common_template.heads.omit()
        return common_template

    def create_admin_template(self, file_name, render_fn = None, real_id=None):
        """
        Make an administrator template.
        """
        admin_banner = self.make_template (self.dummy_render, self.admin_banner_file)
        return self.create_template(file_name, admin_banner, render_fn, real_id)

    def create_user_template(self, file_name, render_fn = None, real_id=None):
        """
        Make a user template.
        """
        user_banner = self.make_template (self.dummy_render, self.user_banner_file)
        return self.create_template(file_name, user_banner, render_fn, real_id)

##### Options Template #####

def render_options(template, flax_data):

    log_settings = flax_data.log_settings

    def fill_log_events(node, event):
        # the empty string can be used to name the root logger
        name = event if event else "default"
        node.event_label.content = name
        node.event_select.atts['name'] = name

        def fill_input(inp, level):
            inp.atts["value"] = level
            inp.content = uistrings.log_level(level)
            if log_settings[event] == level:
                inp.atts['selected'] = 'selected'

        node.event_select.event_option.repeat(fill_input, flax_data.log_levels)

    template.main.collection_events.repeat(fill_log_events, sorted(log_settings))

    def fill_meanings(span, level):
        span.raw = uistrings.log_level(level)

    template.main.level_meaning.repeat(fill_meanings, flax_data.log_levels)


##### Search Templates #####

def render_search(template, isAdmin, renderer, collections, advanced=False, formats=[], results=None, selcols=None):

    if isAdmin:
        template.main.banner_search.omit()
    cols = list(collections.itervalues())
    template.main.collections.repeat(render_search_collection, cols, len(cols))
    if results:
        render_search_result(template.main, results, collections, selcols)
        template.main.descriptions.omit()
    else:
        template.main.descriptions.col_descriptions.name_and_desc.repeat(render_collection_descriptions, cols)
        template.main.results.omit()
    if advanced:
        template.main.advanced_holder = renderer._advanced_search_options().body
        def fill_format(node, format):
            node.format_label.content = format
            node.format_checkbox.atts['value'] = format
            node.format_checkbox.atts['checked'] = 'on'

        template.main.advanced_holder.formats.repeat(fill_format, formats)
    else:
        template.main.advanced_holder.omit()

def render_collection_descriptions(node, collection):
    node.name.content = collection.name
    node.description.content = collection.description

def render_search_collection (node, collection, collection_len, selected=None):
    node.col_name.content = collection.name
    if collection_len == 1:
        node.col_select.omit()
    else:
        node.col_select.atts['value'] = collection.name
        if selected and collection.name in selected:
            node.col_select.atts['checked'] = 'true'

##### Collection List Template #####

def render_collections_list(template, collections, base_url, indexer):
    template.main.atts['action'] = base_url + '/add/'

    # HACK - sort collections by name
    collections = [(c.name, c) for c in collections]
    collections.sort()
    collections = [c[1] for c in collections]
    
    template.main.collection.repeat(render_collection, collections, base_url, indexer)

def render_collection(node, collection, base_url, indexer):

    node.delete_form.atts['action']='/admin/collections/%s/delete' % collection.name

    col_url = base_url + '/' + collection.name + '/view'
    node.name.content = collection.name
    node.name.atts['href'] = urllib.quote(col_url)
    node.description.content = collection.description

    indexing, file_count, error_count = indexer.indexing_info(collection)
    node.doc_count.content = str(collection.document_count)
    node.file_count.content = str(file_count)
    node.error_count.content = str(error_count)
    node.status.content = str("Yes" if indexing else "No")

    node.due_form.atts['action']='/admin/collections/%s/toggle_due' % collection.name
    node.due_form.due_button.content = str(collection.indexing_due)
    node.held_form.atts['action']='/admin/collections/%s/toggle_held' % collection.name
    node.held_form.held_button.content = str(collection.indexing_held)


###### Collection Detail Template ######


def script_for_mappings(col):

    if col:
        maps =  '\n'.join([('   add_mapping("%s", "%s");' % (p, col.mappings[p])).encode('string-escape')
                           for p in col.paths])
    else:
        maps = ""
    maps += '\n   add_mapping("", "");'
    return "\nvar make_mappings = function(){\n %s \n}\n window.onload=make_mappings\n" % maps


# This actually sucks a bit, really we want to make all the checkbox
# and associated labels nodes at initialization time, and then just
# set the checked attributes at render time, but the public api for
# HTMLTemplate doesn't really support that - the repeat thing builds
# new structure, really we want a way of iterating over the already
# built items to set the checked value.

def render_collection_detail(template, collection, formats, languages):
    template.main.script.raw = script_for_mappings(collection)
    if collection:
        template.title.col_name.content = collection.name
    body = template.main
    body.main_form.atts['action'] = 'update' if collection else 'new'
    form = body.main_form

    if collection:
        form.name.content = collection.name
        form.description.atts['value'] = collection.description
        form.col.raw=""

    def fill_format(node, format):
        node.format_label.content = format
        node.format_checkbox.atts['value'] = format
        if collection:
            if format in collection.formats:
                node.format_checkbox.atts['checked'] = 'on'

    form.formats.repeat(fill_format, formats)

    oldest_lookup = {None: form.none,
                     datetime.timedelta(1): form.one_day,
                     datetime.timedelta(7): form.one_week,
                     datetime.timedelta(30): form.one_month,
                     datetime.timedelta(182): form.six_months,
                     datetime.timedelta(365): form.one_year}
    if collection:
        oldest_lookup[collection.oldest].atts['selected']='selected'


    def fill_languages(node, val):
        node.atts["value"] = val[0]
        node.content = val[1]
        if collection and val[0] == collection.language:
            node.atts['selected'] = "selected"

    form.language_option.repeat(fill_languages, languages)
    if collection:
        form.stopwords.atts["value"] = " ".join(collection.stopwords)


    if collection:
        def render_spec(spec):
            sep = ', '
            if isinstance(spec, str):
                return spec
            return sep.join(map(str, spec))

        form.mins.atts['value'] = render_spec(collection.mins)
        form.hours.atts['value'] = render_spec(collection.hours)
        form.monthdays.atts['value'] = render_spec(collection.monthdays)
        form.weekdays.atts['value'] = render_spec(collection.weekdays)
        form.months.atts['value'] = render_spec(collection.months)


###### Search Result Rendering ######
# used from render_search

def render_searched_collection(node, col):
    node.content = col

def render_search_result (node, results, collections, selcols):
    # collections is the list of available collections
    # selcols is a list of selected collections

    query = results.query
    if isinstance(query, types.StringType):
        q_or_ids = "?query=%s" % urllib.quote_plus (query)
        node.query.atts['value'] = query
    else:
        q_or_ids = "?doc_id=%s&col_id=%s" % (urllib.quote_plus(query[1]), urllib.quote_plus(query[0].name))

    if results.is_results_corrected:
        node.results.corrected.raw = \
            uistrings.msg('auto_spell_corrected_msg') % \
            results.spell_corrected_query
    elif (results.spell_corrected_query and
          (not (results.spell_corrected_query == results.query))):
         node.results.corrected.raw = uistrings.msg('spell_suggestion_msg') % {
             "uri": "search?query=" + urllib.quote_plus(results.spell_corrected_query),
             "corrected": results.spell_corrected_query,
         }
    else:
        node.results.corrected.omit()


    def fill_results(node, res):
        # res is xapian results object
        if 'filename' in res.data and 'collection' in res.data:
            filename = res.data['filename'][0]
            collection = res.data['collection'][0]
            url = collections[collection].url_for_doc(filename)
            if 'title' in res.data:
                title = res.data['title'][0].encode('utf-8')
            else:
                if url != "":
                    title = url
                else:
                    title = filename
            node.res_link.atts['href'] = url
            node.res_link.content = '%d. %s' % (res.rank + 1, title)
            node.sim_link.atts['href'] = './search?doc_id=%s&col_id=%s' % (filename, collection)

        if 'content' in res.data:
            node.res_content.raw = res.summarise('content', hl=('<strong>','</strong>'))

        size = res.data.get ('size')
        node.res_size.content = format_size (size[0]) if size else 'unknown'
        mtime = res.data.get ('mtime')
        node.res_mtime.content = format_date (mtime[0]) if mtime else 'unknown'

    cols = list(collections.itervalues())
    node.collections.repeat (render_search_collection, cols, len(cols), selcols)

    xr = results.xap_results
    res_node = node.results
    if xr is None:
        # No collections to search
        node.info.content = 'No collections to search'
        node.nav.omit()
    elif xr.startrank < xr.endrank:
        res_node.results.repeat(fill_results, results.xap_results)
        res_node.info.content = '%s to %s of %s%d matching documents' % (
            xr.startrank + 1, xr.endrank,
            '' if xr.estimate_is_exact else 'about ',
            xr.matches_human_readable_estimate)

        if xr.startrank:
            res_node.nav.first_page.atts['href'] = q_or_ids
            res_node.nav.prev_page.atts['href'] = '%s&tophit=%d' % (q_or_ids,
                xr.startrank - results.maxhits)
        else:
            res_node.nav.first_page.atts['class'] = 'link_disabled'
            res_node.nav.prev_page.atts['class'] = 'link_disabled'

        if xr.more_matches:
            res_node.nav.next_page.atts['href'] = '%s&tophit=%d' % (q_or_ids,
                xr.startrank + results.maxhits)
        else:
            res_node.nav.next_page.atts['class'] = 'link_disabled'
    else:
        # no search results
        res_node.info.content = 'No matching documents found'
        res_node.nav.omit()

KB1 = 1024.0
MB1 = KB1 * KB1
GB1 = MB1 * KB1
TB1 = GB1 * KB1

def format_size (data):
    """
    Return a nicely-formatted string for size data
    """
    data = int (data)
    if data < KB1:
        return '%dB' % data
    elif data < MB1:
        return '%.2fK' % (data / KB1)
    elif data < GB1:
        return '%.2fM' % (data / MB1)
    elif data < TB1:
        return '%.2fG' % (data / GB1)
    else:
        return '%.2fT' % (data / TB1)

def format_date (data):
    """
    Return a nicely-formatted string for date data.
    """
    data = float (data)
    return time.asctime (time.localtime (data))

class Renderer(object):
    """Object providing methods for rendering the templates.

    """
    def __init__(self, template_dir):
        self._tman = TemplateManager(template_dir)

    def index_render(self, *args):
        "Render the admin index page."
        return self._tman.create_admin_template("index.html").render(*args)

    def options_render(self, *args):
        "Render the global options page."
        return self._tman.create_admin_template("options.html", render_options).render (*args)

    def admin_search_render(self, *args):
        "Render the administrator search page."
        return self._tman.create_admin_template("search.html", render_search).render(True, self, *args)

    def user_search_render(self, *args):
        "Render the user search page."
        return self._tman.create_user_template("search.html", render_search).render(False, self, *args)

    def collection_list_render(self, *args):
        "Render the collection listing admin page."
        return self._tman.create_admin_template("collections.html", render_collections_list).render (*args)

    def collection_detail_render(self, *args):
        "Render the collection detail admin page."
        return self._tman.create_admin_template("collection_detail.html", render_collection_detail).render (*args)

    def admin_advanced_search_render(self, *args):
        "Render the administrator search results page."
        return self._tman.create_admin_template("search.html", render_search, real_id="advsearch").render (True, self, *args)

    def user_advanced_search_render(self, *args):
        "Render the user search results page."
        return self._tman.create_user_template("search.html", render_search, real_id="advseach").render (False, self, *args)

    def _advanced_search_options(self):
        "Get a template for rendering the advanced search options"
        return self._tman.make_template(self._tman.dummy_render, "advanced_search.html")
