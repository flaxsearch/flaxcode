import copy
import sys
import os
sys.path.append('..')
sys.path.append('../indexserver')


# tests/experiments related to issue 71
# http://code.google.com/p/flaxcode/issues/detail?id=71

# try running this and see what happens to memory use.  If this keeps
# eating memory then the problem is probably not specifically to do
# with the ifilter_filter.

import remote_filter
def filter_forever():

    s = ' '.join((str(x) for x in xrange(100000)))
    def filter(filename):
        for x in xrange(50):
            yield ('content', copy.copy(s))

    rf = remote_filter.RemoteFilterRunner(filter)
        
    while 1:
        stuff = list(rf('dummy'))
        if not rf.server:
            print "no server"
            break
