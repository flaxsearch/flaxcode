# standard python library imports
import datetime
import random
import os


dir = os.path.dirname(os.path.abspath(os.path.normpath(__file__)))
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
cols.new_collection("foo", 
                    description = "foo description",
                    paths = ["/usr/share/doc"],
                    formats = ["txt", "doc"],
                    indexed = datetime.date.today(),
                    queries = random.randrange(100000),
                    docs = random.randrange(100000),
                    status = 0)

cols.new_collection("bar",
                    paths = ['%s/My Documents/'% os.path.expanduser('~')])


class FlaxOptions(object):
    """
    global options for Flax
    """
    
    # use __slots__ to ensure that we don't pass in things here that
    # we don't expect
    
    __slots__ = ("collections", "db_dir", "flax_dir", "formats", "log_events", "log_levels", "log_settings", 
                 "filters", "filter_settings", "languages")

    def __init__(self, collections, db_dir, flax_dir, formats, 
                 log_events, log_levels, log_settings, 
                 filters, filter_settings, languages):
        self.collections = collections
        self.db_dir = db_dir
        self.flax_dir = flax_dir
        self.formats = formats
        self.log_events = log_events
        self.log_levels = log_levels
        self.log_settings = log_settings
        self.filters = filters
        self.filter_settings = filter_settings
        self.languages = languages


options = FlaxOptions(cols, 
                      db_dir, 
                      dir, 
                      formats, 
                      log_events, 
                      event_levels, 
                      log_settings,
                      filters,
                      filter_settings,
                      languages)

