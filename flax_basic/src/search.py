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
"""Build and perform searches according to user input.

"""
__docformat__ = "restructuredtext en"

import logging
import types

import flax
import util

class Results (object):
    """ Make search results from supplied query information.

    `dbnames` the names of the databases queried to get the results.
    `xap_query`: The xapian query that produced the results.
    `xap_results`: The xappy list of SearchResult objects.
    `query`: The string query or (collection, doc_id) pair.
    `exact`: A phrase to be searched for exactly.
    `exclusions`: a list of words that should not appear in the results.
    `spell_corrected_query`: The spell corrected query is there is one.
    `is_results_corrected`: if results is for the spell_corrected_query rather than original_query
    `tophit`: rank of the first result in results
    `maxhits`: max number of results
    `sort_by`: how to order the results.
    """

    log = logging.getLogger("searching")

    sort_map = {None: None,
                '1' : None,
                '2' : '-mtime',
                '3' : 'mtime'}

    def __init__(self, query, exact, exclusions, formats, dbnames,
                 tophit, maxhits, sort_by):

        if len(dbnames) == 0:
            self.query = query
            self.is_results_corrected = False
            self.spell_corrected_query = None
            self.xap_results = None
            return

        self.exclusions = exclusions
        self.exact = exact
        self.formats = formats
        self.dbnames = dbnames
        self.query = query
        self.tophit = tophit
        self.maxhits = maxhits

        self.sort_by = self.sort_map[sort_by]

        conn = self.conn_for_dbs(dbnames)
        is_string_query = isinstance(query, types.StringType)
        if is_string_query:
            self.xap_query, self.highlight_query = self.make_xap_query(
                conn, query, exact, exclusions, formats)
            corrected = conn.spell_correct(self.query)
            self.spell_corrected_query = (corrected if corrected != query
                                          else None)

        else:
            conn_for_sim = query[0].search_conn()
            self.xap_query = conn_for_sim.query_similar([query[1]])
            self.highlight_query = self.xap_query
            self.spell_corrected_query = None

        self.do_search(conn)

        self.is_results_corrected = False
        if (self.xap_results.matches_upper_bound == 0 and
            self.spell_corrected_query):

            self.xap_query = conn.query_parse(self.spell_corrected_query)
            self.do_search(conn)
            if self.xap_results.matches_upper_bound != 0:
                self.is_results_corrected = True
            else:
                self.spell_corrected_query = None

    def make_xap_query(self, conn, query, exact, exclusions, formats):
        """Make the xapian query for a given set of search parameters.

        Returns a pair: (xap_query, highlight_query), where xap_query is the
        query to be used to perform the search, and highlight_query is a query
        to be used for highlighting.

        """
        if not any((query, exact, exclusions, formats)):
            empty_query = conn.query_none()
            return empty_query, empty_query

        # Work out "hq", which is the positive and textual parts of the query,
        # used for highlighting.
        if query:
            hq = conn.query_parse(query)
        else:
            hq = conn.query_all()
        if exact:
            hq = conn.query_composite(conn.OP_AND, (hq, conn.query_parse( '"%s"' % exact)))

        # Work out xq, which is the actual query to be executed, but adding the
        # filters and filetypes.
        xq = hq
        if exclusions:
            xq = conn.query_filter(xq, conn.query_parse( ' '.join(util.listify(exclusions))), True )
        if formats:
            filetype_queries = [conn.query_field('filetype', format) for format in util.listify(formats)]
            xq = conn.query_filter(xq, conn.query_composite(conn.OP_OR, filetype_queries))
        return xq, hq

    def do_search(self, conn):
        self.log.info("Search databases %s with query %s" %
                      (self.dbnames, self.xap_query))
        self.xap_results = conn.search(self.xap_query,
                                       self.tophit,
                                       self.tophit + self.maxhits,
                                       100,
                                       sortby=self.sort_by)

    def conn_for_dbs(self, dbnames):
        return flax.options.collections.get_search_connection(dbnames)

def search(query, exact, exclusions, formats, dbnames,
           tophit = 0, maxhits = 10, sort_by=None):
    """Search the xapian databases at the paths listed in `dbnames` with `query`.
    
    Return a Results() object holding the results of the search.

    Spell correction occurs only when `query` is a string (rather than a query
    object).

    If spell correction occured and the results for the original query were
    empty then the results are for the spell corrected query.

    """
    return Results(query, exact, exclusions, formats, dbnames,
                   tophit, maxhits, sort_by)
