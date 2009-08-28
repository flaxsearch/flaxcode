import sys
import flax.searchclient

# open a connection to Flax Server
conn = flax.searchclient.Client('http://localhost:8080')

# get a reference to the database
db = conn.db('books')

# do the search and get the results
results = db.search_structured(filter=['author:%s' % sys.argv[1]])

# print a summary of the results
print '%d to %d of %s results' % (results.start_rank + 1, 
    results.end_rank,
    results.matches_human_readable_estimate)

# print the rank and title of each result
for hit in results.results:
    print '%s. %s' % (hit.rank + 1, hit.data['title'][0])