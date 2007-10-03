import os
import time
import sys
sys.path.append('..')
import util

class FileWatcher(util.DelayThread):
    """ Watches a file for modification and notifies when such changes
        occur by calling a supplied callable.  We don't deal with
        non-existent files or cope with file deletion.
    """
    
    def __init__(self, filename, change_action,  **kwargs):
        util.DelayThread.__init__(self, **kwargs)
        self.filename = filename
        self.mtime = os.path.getmtime(filename)
        self.change_action = change_action

    def action(self):
        new_mtime = os.path.getmtime(self.filename)
        if new_mtime > self.mtime:
            self.mtime = new_mtime
            self.change_action()

if __name__ == "__main__":
    import sys
    import time
    filename = sys.argv[1]
    def print_changed():
        print "File: %s has changed" % filename

    FileWatcher(filename, print_changed, delay=1).start()
    while True:
        time.sleep(1)
