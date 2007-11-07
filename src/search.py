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

import xappy
import xapian

import util

# Searching multiple databases depends on using xapian facilities not
# available via xappy. We use the xappy SearchConnection's internal
# handle on the xapian connection and invoke its add_database
# property.

class Results (object):
    """ Make search results from supplied query information.

    `dbs` the databases queried to get the results.
    `xap_query`: The xapian query that produced the results.
    `xap_results`: The xappy list of SearchResult objects.
    `query`: The string query or (collection, doc_id) pair.
    `exact`: A phrase to be searched for exactly.
    `exclusions`: a list of words that should not appear in the results.
    `spell_corrected_query`: The spell corrected query is there is one.
    `is_results_corrected`: if results is for the spell_corrected_query rather than original_query
    `tophit`: rank of the first result in results
    `maxhits`: max number of results
    """

    log = logging.getLogger("searching")

    def __init__(self, query, exact, exclusions, formats, dbs, tophit, maxhits):

        if len(dbs) == 0:
            self.query = query
            self.is_results_corrected = False
            self.spell_corrected_query = None
            self.xap_results = None
            return

        self.exclusions = exclusions
        self.exact = exact
        self.formats = formats
        self.dbs = dbs
        self.query = query
        self.tophit = tophit
        self.maxhits = maxhits

        conn = self.conn_for_dbs(dbs)
        is_string_query = isinstance(query, types.StringType)
        if is_string_query:
            self.xap_query, self.highlight_query = self.make_xap_query(conn, query, exact, exclusions, formats)
            corrected = conn.spell_correct(self.query)
            self.spell_corrected_query = corrected if corrected != query else None

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
            hq = conn.query_composite(xappy.SearchConnection.OP_AND, (hq, conn.query_parse( '"%s"' % exact)))

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
        self.log.info("Search databases %s with query %s" % (self.dbs, self.xap_query))
        self.xap_results = conn.search(self.xap_query,
                                       self.tophit,
                                       self.tophit + self.maxhits,
                                       100)

    def conn_for_dbs(self, dbs):
        conn = xappy.SearchConnection(dbs[0])
        for d in dbs[1:]:
            conn._index.add_database(xapian.Database(d))
        return conn

def search(query, exact, exclusions, formats, dbs, tophit = 0, maxhits = 10):
    """ search the xapian dbs named by `dbs` with `query`.  return a
        triple (results, corrected_query, corrected_results), where
        results is the xapian results object, corrected query is a
        spell corrected version of the oringinal query and corrected
        results is a boolean flag indicating whether the results are
        for the corrected query or the orgiginal query.

        Spell correction occurs when `query` is a string (rather than
        a query object).

        If spell correction occured and the results for the original
        query were empty then the results are for the spell corrected
        query.

    """
    return Results(query, exact, exclusions, formats, dbs, tophit, maxhits)
