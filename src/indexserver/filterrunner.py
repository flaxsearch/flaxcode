"""
Program to run filters and communicate their output.

This is indented to be run as a subprocess for the main indexing
process, so as to protect it against badly behaved filters.

The program starts expects a single argument being a
moduldename.filter pattern. It attempts to import the module named by
modulname and checks that it contains a callable named by filter. If
not then it exits immediately.

All communication is via stdin and stdout. All communication consists
of a long, n, packed as struct('L', n) followed by n bytes of data
being a pickled representation of a python object. We will elide this
detail and just talk about the underlying objects, trusting that the
pickling is working underneath.

We wait for a filename on standard input. We call the filter on the
file, writing the resultant blocks to standard output. Once the
iteration finishes we return the empty string and wait for more input.
Exceptions are caught and returned.

"""


import sys
sys.path.append('..')
from util import IO

def find_filter(filter_spec):
    mod_name, obj_name = filter_spec.split('.')
    mod = __import__(mod_name)
    obj = getattr(mod, obj_name)
    if not callable(obj):
        raise TypeError("Need a callable")
    else:   
        return obj

def startup():
    try:
        filter = find_filter(sys.argv[1])
    except IndexError, e:
        print 'Usage: supply "module.filter" on the command line'
    except TypeError, e:
        print "I need a (callable) filter"

    io = IO()
    while 1:
        file_name = io.receive()
        for block in filter(file_name):
            io.send(block)
        io.send("")

if __name__ == "__main__":
    startup()
