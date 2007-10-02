import os
import threading

class FileWatcher(threading.Thread):
    """ Watches a file for modification and notifies when such changes
        occur by calling a supplied function passing in the file.  We
        don't deal with non-existent files or cope with file deletion.
    """
    
    def __init__(self, stop, filename, action, delay=5):

        threading.Thread.__init__(self)
        self.stop = stop
        self.filename = filename
        self.mtime = os.path.getmtime(filename)
        self.action = action
        self.delay = delay

    def run(self):

        while True:
            if self.stop.isSet():
                break
            new_mtime = os.path.getmtime(self.filename)
            if new_mtime > self.mtime:
                self.mtime = new_mtime
                self.action()
            self.stop.wait(self.delay)


if __name__ == "__main__":
    import sys
    import time
    filename = sys.argv[1]
    def print_changed():
        print "File: %s has changed" % filename

    stop = threading.Event()
    stop.clear()
    FileWatcher(stop,  filename, print_changed, delay=1).start()
    try:
        while True:
            time.sleep(1)
    except:
        stop.set()
