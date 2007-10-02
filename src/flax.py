from __future__ import with_statement
# standard python library imports
import datetime
import logging
import random
import os
import ConfigParser

import logclient

class FlaxOptions(object):
    """
    global options for Flax
    """
    
    def __init__(self, collections, db_dir, flax_dir, formats, 
                 logger_names, filters, filter_settings, languages):
        
        self.collections = collections
        self.db_dir = db_dir
        self.flax_dir = flax_dir
        self.formats = formats
        self.logger_names = logger_names
        self.filters = filters
        self.filter_settings = filter_settings
        self.languages = languages

    def _set_log_settings(self, vals):
        new_levels = {}
        for name in self.logger_names:
            if name in vals:
                new_levels[name] = vals[name]
        if "default" in vals:
            new_levels[""] =  vals["default"]

        lq = logclient.LogQuery()
        lq.set_levels(new_levels)

    def _get_log_settings(self):
        # is .level part of the public api for logger objects?
        return dict((name, logging.getLevelName(logging.getLogger(name).level)) for name in self.logger_names)

    log_settings = property(fset = _set_log_settings, fget = _get_log_settings, doc = """
    A dictionary mapping log event names to log levels.  It is
    permitted for the dictionary to contain names that do not name a
    log event, such will be  silently ignored.""")

    @property
    def log_levels(self):
        return map(logging.getLevelName,  [0,10,20,30,40,50])

def make_options():
    #dir = os.path.dirname(os.path.abspath(os.path.normpath(__file__)))
    dir = os.getcwd()
    user = os.path.expanduser('~')

    db_dir = os.path.normpath(dir+'/dbs') 

    logger_names = ("",
                    "collections",
                    "indexing",
                    "filtering",
                    "filtering.ifilter",
                    "filtering.simpletext",
                    "searching")

    filters = ["IFilter", "Xapian", "Text"]
    
    formats = ["txt", "doc", "html", "pdf", "xsl", "ppt"]
    formats.sort()
    
    filter_settings = dict( (f, filters[0]) for f in formats)

    languages = [ ("none",  "None"),
                  ("da",  "Danish"),
                  ("nl", "Dutch"),
                  ("en", "English"),
                  ("lovins", "English (lovins)"),
                  ("porter", "English (porter)"),
                  ("fi", "Finnish"),
                  ("fr", "French"),
                  ("de", "German"),
                  ("it", "Italian"),
                  ("no", "Norwegian"),
                  ("pt", "Portuguese"),
                  ("ru", "Russian"),
                  ("es", "Spanish"),
                  ("sv", "Swedish")]
              
              

    import flax_collections

    cols = flax_collections.FlaxCollections(db_dir)

    return FlaxOptions(cols, 
                       db_dir, 
                       dir, 
                       formats, 
                       logger_names,
                       filters,
                       filter_settings,
                       languages)

# placeholder for global options object
options = None

