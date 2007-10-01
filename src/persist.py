from __future__ import with_statement
import shelve
import threading
import time
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


data_changed = threading.Event()
data_changed.clear()

class DataSaver(threading.Thread):
    """ thread to periodically save data """
    def __init__(self, filename, delay=5):
        threading.Thread.__init__(self)
        self.delay=delay
        self.filename=filename
        self.stop = threading.Event()
        self.stop.clear()

    def run(self):
        while not self.stop.isSet():
            if data_changed.isSet():
                store_flax(self.filename, flax.options)
                data_changed.clear()
            time.sleep(self.delay)

    def join(self, timeout=None):
        self.stop.set()
        threading.Thread.join(self, timeout)
