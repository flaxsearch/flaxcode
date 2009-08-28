import sys
import flax.searchclient

# open a connection to Flax Server
conn = flax.searchclient.Client('http://localhost:8080')

# get a reference to the database
db = conn.db('books')

# print the info
print db.info