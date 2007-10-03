from __future__ import with_statement
import shelve
import threading
import time
import flax
import util

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

class DataSaver(util.DelayThread):
    """ thread to periodically save data """

    def __init__(self, filename, **kwargs):
        self.filename=filename
        util.DelayThread.__init__(self, **kwargs)

    def action(self):
        if data_changed.isSet():
            store_flax(self.filename, flax.options)
            data_changed.clear()


