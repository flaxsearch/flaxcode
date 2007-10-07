import os
import time
import sys
sys.path.append('..')
from util import FileWatcher


if __name__ == "__main__":
    import sys
    import time
    filename = sys.argv[1]
    def print_changed():
        print "File: %s has changed" % filename

    FileWatcher(filename, print_changed, delay=1).start()
    while True:
        time.sleep(1)
