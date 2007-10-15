import logging
import types

import xappy
import xapian

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
    `spell_corrected_query`: The spell corrected query is there is one.
    `is_results_corrected`: if results is for the spell_corrected_query rather than original_query
    `tophit`: rank of the first result in results
    `maxhits`: max number of results
    """

    log = logging.getLogger("searching")

    def __init__(self, query, dbs, tophit, maxhits):

        if len(dbs) == 0:
            self.query = query
            self.is_results_corrected = False
            self.spell_corrected_query = None
            self.xap_results = None
            return
        
        self.dbs = dbs
        self.query = query
        self.tophit = tophit
        self.maxhits = maxhits

        conn = self.conn_for_dbs(dbs)
        is_string_query = isinstance(query, types.StringType)
        if is_string_query:
            self.xap_query = conn.query_parse(query)
            corrected = conn.spell_correct(self.query)
            self.spell_corrected_query = corrected if corrected != query else None

        else:
            conn_for_sim = query[0].search_conn()
            self.xap_query =  conn_for_sim.query_similar([query[1]])
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

    def do_search(self, conn):        
        self.log.info("Search databases %s with query %s" % (self.dbs, self.xap_query))
        self.xap_results = conn.search(self.xap_query, self.tophit, self.tophit + self.maxhits)

    def conn_for_dbs(self, dbs):
        conn = xappy.SearchConnection(dbs[0])
        for d in dbs[1:]:
            conn._index.add_database(xapian.Database(d))
        return conn

def search(query, dbs, tophit = 0, maxhits = 10):
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
    return Results(query, dbs, tophit, maxhits)
