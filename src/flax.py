# standard python library imports
import datetime
import random
import os


# flax imports
import collection

_dir = os.path.dirname(os.path.abspath(os.path.normpath(__file__)))

_collections = collection.collections()

_collections.new_collection("foo", 
                            description = "foo description",
                            paths = ["/usr/share/doc"],
                            formats = ["txt", "doc"],
                            indexed = datetime.date.today(),
                            queries = random.randrange(100000),
                            docs = random.randrange(100000),
                            status = 0)

_collections.new_collection("bar",
                            paths = ['%s/My Documents/'% os.path.expanduser('~')])


# these need to come from elsewhere:
_log_events = ("Create Collection",
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

_event_levels = ("None", "Critical", "Error", "Warning", "Info", "Debug", "All")

_default_level = _event_levels[3]


_log_settings = dict( (e, _default_level) for e in _log_events)

_filters = ["IFilter", "Xapian"]

_formats = ("txt", "doc", "html")

_filter_settings = dict((f, _filters[0]) for f in _formats)



class FlaxOptions(object):
    """
    global options for Flax
    """
    
    # use __slots__ to ensure that we don't pass in things here that
    # we don't expect
    
    __slots__ = ("collections", "db_dir", "flax_dir", "formats", "log_events", "log_levels", "log_settings", 
                 "filters", "filter_settings")

    def __init__(self, collections, db_dir, flax_dir, formats, 
                 log_events, log_levels, log_settings, 
                 filters, filter_settings):
        self.collections = collections
        self.db_dir = db_dir
        self.flax_dir = flax_dir
        self.formats = formats
        self.log_events = log_events
        self.log_levels = log_levels
        self.log_settings = log_settings
        self.filters = filters
        self.filter_settings = filter_settings


options = FlaxOptions(_collections, 
                      os.path.normpath(_dir+'/dbs'), 
                      _dir, 
                      _formats, 
                      _log_events, 
                      _event_levels, 
                      _log_settings,
                      _filters,
                      _filter_settings) 
