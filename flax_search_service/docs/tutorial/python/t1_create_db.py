import flax.searchclient

# open a connection to Flax Server
conn = flax.searchclient.Client('http://localhost:8080')

# create a database, overwriting any existing db with the same name
conn.create_database('books', overwrite=True)

# create a database schema
schema = conn.schema('books')

# add some field definitions
schema.add_field('title', {'freetext': {'language': 'en'}, 'store': True})
schema.add_field('first', {'freetext': {'language': 'en'}, 'store': False})
schema.add_field('author', {'exacttext': True, 'store': True})
