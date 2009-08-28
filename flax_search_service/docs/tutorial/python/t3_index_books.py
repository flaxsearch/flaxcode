import sys
import re
import flax.searchclient

# open a connection to Flax Server
conn = flax.searchclient.Client('http://localhost:8080')

# get a reference to the database
db = conn.db('books')

# create a regexp to parse book data
bookfield_re = re.compile('(\w+):\s+(.+)')

# read books data from file
f = open(sys.argv[1])

# documents are dicts with fieldnames as keys and strings (or lists of
# strings) as values
doc = {}

for line in f:
    match = bookfield_re.match(line)
    if match:
        name = match.group(1)
        value = match.group(2)
        if name == 'isbn':
            # add the document, using ISBN as the ID
            db.add_document(doc, value)
            doc = {}
        else:
            # add the field to the document
            doc[name] = value

f.close()

# commit the documents to the database
db.flush()

