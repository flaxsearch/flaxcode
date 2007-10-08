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
import processing
import functools

def filter_runner(filter, i, o):
    "Repeatedly receive a filename on `i`, run filter on that file, send output to `o`"
    while 1:
        filename = i.recv()
        results = list(filter(filename))
        o.send(list(filter(filename)))

class TimeOutError(Exception):
    "Signal that a remote filter is taking too long to process a file"
    pass

class RemoteFilterRunner(object):
    """
    A filter that runs another filter in a subprocess, with a timeout.
    """

    def __init__(self, filter, timeout=5):
        self.filter = filter
        self.timeout = timeout
        self.server=None

    def __call__(self, file_name):
        self.maybe_start_server()
        self.outpipe[0].send(file_name)
        if self.inpipe[1].poll(self.timeout):
            blocks = self.inpipe[1].recv()
            for block in blocks:
                yield block
        else:
            self.server.terminate()
            self.server = self.i = self.o =None
            raise TimeOutError("The server took to long to process file %s, giving up" % file_name)
        
    def maybe_start_server(self):
        if not self.server:
            self.inpipe = processing.Pipe()
            self.outpipe = processing.Pipe()
            self.server = processing.Process(target = filter_runner, args = [ self.filter, self.outpipe[1], self.inpipe[0]])
            self.server.setDaemon(True)
            self.server.start()

# just for expermenting/testing

if __name__ == "__main__":

    def forever_filter(filename):
        while 1:
            pass

    def find_filter(filter_spec):
        mod_name, obj_name = filter_spec.split('.')
        mod = __import__(mod_name)
        obj = getattr(mod, obj_name)
        if not callable(obj):
            raise TypeError("Need a callable")
        else:
            return obj        

    filter = RemoteFilterRunner(find_filter(sys.argv[1]))
    while 1:
        filename = raw_input("Filename to filter: ")
        if filename == '0':
            break
        else:
            print "invoking filter"
            blocks = filter(filename)
            print "blocks are:"
            print list(blocks)
    


