import logging
import types

import xappy
import xapian

# Searching multiple databases depends on using xapian facilities not
# available via xappy. We use the xappy SearchConnection's internal
# handle on the xapian connection and invoke its add_database
# property.


def search(dbs, query, tophit = 0, maxhits = 10):
    log = logging.getLogger("searching")
    log.info("Search databases %s with query %s" % (dbs, query))
    conn = xappy.SearchConnection(dbs[0])
    for d in dbs[1:]:
        conn._index.add_database(xapian.Database(d))
    query = conn.query_parse(query)
    return conn.search (query, tophit, tophit + maxhits)

def sim_query(collections, col, doc_id):
    conn = xappy.SearchConnection(collections[col].dbname())
    return unparse(conn.query_similar([doc_id]))

# FIXME: make this do the right thing
def unparse(q):
    return "Well, this is not what you want is it? :/"
