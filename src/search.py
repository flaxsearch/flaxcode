import logging
import types

import xappy
import xapian

# Searching multiple databases depends on using xapian facilities not
# available via xappy. We use the xappy SearchConnection's internal
# handle on the xapian connection and invoke its add_database
# property.


def conn_for_dbs(dbs):
    conn = xappy.SearchConnection(dbs[0])
    for d in dbs[1:]:
        conn._index.add_database(xapian.Database(d))
    return conn

def search(dbs, query, tophit = 0, maxhits = 10):
    log = logging.getLogger("searching")
    conn = conn_for_dbs(dbs)
    if isinstance(query, str):
        query = conn.query_parse(query)
    log.info("Search databases %s with query %s" % (dbs, query))
    return conn.search (query, tophit, tophit + maxhits)

def sim_query(collections, dbs, col_id, doc_id, tophit=0, maxhits=10):
    conn = xappy.SearchConnection(collections[col_id].dbname())
    query =  conn.query_similar([doc_id])
    return search(dbs, query, tophit, maxhits)

