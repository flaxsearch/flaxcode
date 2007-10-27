"""Filters for testing, not imported by main code"""

def loop_for_ever_filter(filename):
    while 1:
        pass

import remote_filter
remote_loop_for_ever_filter = remote_filter.RemoteFilterRunner(loop_for_ever_filter)
