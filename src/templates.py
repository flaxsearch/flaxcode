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
"""HTMLTemplates for Flax and rendering thereof.

"""
from __future__ import with_statement
__docformat__ = "restructuredtext en"

import os
import urllib
import datetime
import time
import types
import functools

import HTMLTemplate

import uistrings
import util
import version

# Cause HTMLTemplate to discard all XML comments.
# This is a bit nasty, but HTMLTemplate development seems to have ceased, and
# there's no-one to submit changes to: so the options are to start maintaining
# our own fork of HTMLTemplate, or to patch it on the fly like this.
def my_handle_comment(self, txt): pass
HTMLTemplate.Parser.handle_comment = my_handle_comment
del my_handle_comment


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

    def make_template(self, render_fn, file_name, nav_id=None):
        """
        Make an HTMLTemplate from `file_name` in `template_dir` using `render_fn`.

        """
        fpath = os.path.join (self.template_dir, file_name)
        mtime = os.path.getmtime(fpath)
        key = (file_name, render_fn, nav_id)
        try:
            cached = self._cache[key]
            if cached[1] == mtime:
                return cached[0]
        except KeyError:
            pass

        t = HTMLTemplate.Template(render_fn, open(fpath).read())
        self._cache[key] = (t, mtime)
        return t

    def create_template(self, file_name, banner, render_fn=None, nav_id=None):
        """Create a template.

        :Parameters:
           - `file_name`: The name of the file in the template directory to
             read the template from.
           - `banner`: The banner to display at the top of the resulting
             template.  This should be a template.
           - `render_fn`: The function which should be called when the template
             is rendered.  If None, a dummy function which doesn't do
             substitutions will be used.
           - `nav_id`: If not None, change the id attribute for the banner to
             "banner_" + nav_id, to cause the navigation links to highlight a
             specific part of the navigation page.  If None, the banner id will
             be set from the ID attribute of the node named "body".

        """
        fn = render_fn if render_fn else self.dummy_render
        common_template = self.make_template(fn, "flax.html")
        sub_template = self.make_template(self.dummy_render, file_name, nav_id)
        try:
            if not nav_id:
                nav_id = sub_template.body.atts['id']
            banner.banner.atts['id'] = 'banner_' + nav_id
        except (KeyError, AttributeError):
            pass
        common_template.banner.raw = banner.render()

        # Substitute the contents of any title node
        if hasattr(sub_template, 'title'):
            common_template.title = sub_template.title

        common_template.main = sub_template.body
        if hasattr(sub_template, 'heads'):
            common_template.heads = sub_template.heads
        else:
            common_template.heads.omit()
        return common_template

    def create_admin_template(self, file_name, render_fn=None, nav_id=None):
        """Make an administrator template.

        This just calls create_template with a banner template made from the
        admin banner file.

        """
        admin_banner = self.make_template(self.dummy_render, self.admin_banner_file)
        return self.create_template(file_name, admin_banner, render_fn, nav_id)

    def create_user_template(self, file_name, render_fn=None, nav_id=None):
        """Make a user template.

        This just calls create_template with a banner template made from the
        user banner file.

        """
        user_banner = self.make_template(self.dummy_render, self.user_banner_file)
        return self.create_template(file_name, user_banner, render_fn, nav_id)

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

def render_search(template, isAdmin, renderer, advanced, collections, results=None, selcols=None, formats=[]):
    if not advanced:
        template.main.advanced_holder.omit()
    cols = list(collections.itervalues())
    template.main.collections.repeat(render_search_collection, cols, len(cols))
    if results and cols:
        render_search_result(template.main, results, collections, selcols, formats)
        template.main.descriptions.omit()
    else:
        template.main.descriptions.col_descriptions.name_and_desc.repeat(render_collection_descriptions, cols)
        template.main.results.omit()



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


##### About Template #####

def render_about(template, isAdmin):
    """Render the "about" template.

    """
    template.main.version.content = version.get_version_string()


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
    
    if len (collection.description) > 30:   # FIXME a bit arbitrary
        node.description.content = collection.description[:30]
        node.description_more.atts['href'] = 'javascript:alert(%s)' % repr (collection.description)
    else:
        node.description.content = collection.description
        node.description_more.omit()
        
    indexing, file_count, error_count = indexer.indexing_info(collection)
    node.doc_count.content = str(collection.document_count)
    node.doc_count.atts['id'] = '_doc_count_' + collection.name
    
    node.file_count.content = str(file_count)
    node.file_count.atts['id'] = '_file_count_' + collection.name
    
    node.error_count.content = str(error_count)
    node.error_count.atts['id'] = '_error_count_' + collection.name
    
#    node.status.content = str("Yes" if indexing else "No")
#    node.status.atts['id'] = '_status_' + collection.name

    node.due_form.due_button.atts['id'] = '_due_button_' + collection.name
    node.due_form.atts['action']='/admin/collections/%s/toggle_due' % collection.name
    if indexing:
        node.due_form.due_button.content = 'In progress'
        node.due_form.due_button.atts['disabled'] = 'true'
    elif collection.indexing_due:
        node.due_form.due_button.content = 'Scheduled'
        node.due_form.due_button.atts['disabled'] = 'true'
    else:
        node.due_form.due_button.content = 'Start'
    
    node.held_form.atts['action']='/admin/collections/%s/toggle_held' % collection.name
    node.held_form.held_button.content = 'Unhold' if collection.indexing_held else 'Hold'
    node.held_form.held_button.atts['id'] = '_held_button_' + collection.name


###### Collection Detail Template ######


def script_for_mappings(col):

    if col:
        maps =  '\n'.join([('   add_mapping("%s", "%s");' % (p, col.mappings[p])).encode('string-escape')
                           for p in col.paths])
    else:
        maps = ""
    maps += '\n   add_mapping("", "");'
    return "\nvar make_mappings = function(){\n %s \n}\n" % maps


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
        for format in formats:
            if format in collection.formats and format != "htm":
                getattr(form, format).atts['checked'] = 'on'

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

def render_search_result (node, results, collections, selcols, formats):
    # collections is the list of available collections
    # selcols is a list of selected collections

    query = results.query
    is_string_query = isinstance(query, types.StringType)

    if is_string_query:
        q_or_ids = "?query=%s&exact=%s&exclusions=%s&%s" % (
            urllib.quote_plus(query),
            urllib.quote_plus(results.exact or ""),
            urllib.quote_plus(results.exclusions or ""),
            ["format=%s" % urllib.quote_plus(f) for f in results.formats if f != 'htm'] if results.formats else ""
        )
        node.query.atts['value'] = query
        if results.exact:
            node.advanced_holder.exact.atts['value'] = results.exact
        if results.exclusions:
            node.advanced_holder.exclusions.atts['value'] = results.exclusions

        if results.formats:
            for format in util.listify(results.formats):
                if format !='htm':
                    getattr(node.advanced_holder, format).atts['checked'] = 'on'       
    else:
        q_or_ids = "?doc_id=%s&col_id=%s" % (
            urllib.quote_plus(query[1]),
            urllib.quote_plus(query[0].name),
        )

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
        # res is xappy SearchResult object
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
            if is_string_query:
                node.res_content.raw = res.summarise('content', hl=('<strong>','</strong>'))
            else:
                node.res_content.raw = res.summarise('content', hl=('',''))

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
        res_node.info.content = 'No collections to search'
        res_node.nav.omit()
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

    def options_render(self, *args):
        "Render the global options page."
        return self._tman.create_admin_template("options.html", render_options).render (*args)

    def admin_search_render(self, *args):
        "Render the administrator search page."
        return self._tman.create_admin_template("search.html", render_search).render(True, self, False, *args)

    def user_search_render(self, *args):
        "Render the user search page."
        return self._tman.create_user_template("search.html", render_search).render(False, self, False, *args)

    def collection_list_render(self, *args):
        "Render the collection listing admin page."
        return self._tman.create_admin_template("collections.html", render_collections_list).render (*args)

    def collection_detail_render(self, *args):
        "Render the collection detail admin page."
        return self._tman.create_admin_template("collection_detail.html", render_collection_detail).render (*args)

    def admin_advanced_search_render(self, *args):
        "Render the administrator search results page."
        return self._tman.create_admin_template("search.html", render_search, nav_id="advsearch").render(True, self, True, *args)

    def user_advanced_search_render(self, *args):
        "Render the user search results page."
        return self._tman.create_user_template("search.html", render_search, nav_id="advsearch").render(False, self, True, *args)

    def admin_about_render(self, *args):
        "Render the admin About page."
        return self._tman.create_admin_template("about.html", render_about).render(True, *args)

    def user_about_render(self, *args):
        "Render the user About page."
        return self._tman.create_user_template("about.html", render_about).render(False, *args)

