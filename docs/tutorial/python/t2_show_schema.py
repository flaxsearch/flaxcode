import flax.searchclient

# open a connection to Flax Server
conn = flax.searchclient.Client('http://localhost:8080')

# get a reference to the schema
schema = conn.schema('books')

# display the field definitions
for field in schema.get()['fields'].iteritems():
    print field
