from __future__ import with_statement
import shelve

import flax

def store_flax(filename, options):
    d = shelve.open(filename) 
    d['flax'] = options
    d.close()
    
def read_flax(filename):
    d = shelve.open(filename)
    try:
        options = d['flax']
    except KeyError:
        # warning here
        options = flax.make_options()
    d.close()
    return options



