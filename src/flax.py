from __future__ import with_statement
# standard python library imports
import datetime
import random
import os
import ConfigParser


class FlaxOptions(object):
    """
    global options for Flax
    """
    
    def __init__(self, collections, db_dir, flax_dir, formats, 
                 log_events, log_levels, log_settings, 
                 filters, languages):
        
        self.collections = collections
        self.db_dir = db_dir
        self.flax_dir = flax_dir
        self.formats = formats
        self.log_events = log_events
        self.log_levels = log_levels
        self.log_settings = log_settings
        self.filters = filters
        self.languages = languages


def make_options():
    #dir = os.path.dirname(os.path.abspath(os.path.normpath(__file__)))
    dir = os.getcwd()
    user = os.path.expanduser('~')


    db_dir = os.path.normpath(dir+'/dbs') 


    log_events = ("Create Collection",
                  "Modify Collection",
                  "Delete Collection",
                  "Index Collection",
                  "Filter file",
                  "Add to doc",
                  "Remove from doc",
                  "Add to db",
                  "Remove from db",
                  "Run search",
                  "Format results")

    event_levels = ("None", "Critical", "Error", "Warning", "Info", "Debug", "All")

    default_level = event_levels[3]

    log_settings = dict( (e, default_level) for e in log_events)

    filters = ["IFilter", "Xapian", "Text"]
    
    formats = ("txt", "doc", "html")

    filter_settings = dict((f, filters[0]) for f in formats)

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
                       log_events, 
                       event_levels, 
                       log_settings,
                       filter_settings,
                       languages)

# placeholder for global options object
options = None

