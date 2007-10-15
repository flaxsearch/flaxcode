# Copyright (C) 2007 Lemur Consulting Ltd
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""Global options for flax.

"""
__docformat__ = "restructuredtext en"

import logging
import os

import collection_list
import flaxpaths
import logclient

current_version = 7

class FlaxOptions(object):
    """Global options for Flax.

    """    
    def __init__(self, version, formats, 
                 logger_names, filters, filter_settings, languages):

        self.version = version
        self.formats = formats
        self.collections = collection_list.CollectionList(self.formats)
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
            new_levels[""] = vals["default"]

        lq = logclient.LogConf(flaxpaths.paths.logconf_path)
        lq.set_levels(new_levels)

    def _get_log_settings(self):
        # is .level part of the public api for logger objects?
        # FIXME - check
        return dict((name, logging.getLevelName(logging.getLogger(name).level)) for name in self.logger_names)

    log_settings = property(fset=_set_log_settings, fget=_get_log_settings, doc=
        """A dictionary mapping log event names to log levels.
    
        It is permitted for the dictionary to contain names that do not name a log
        event, such will be silently ignored.
    
        """)

    @property
    def log_levels(self):
        """The list of supported logging levels.

        """
        return ('NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

def make_options():
    user = os.path.expanduser('~')
    logger_names = ("",
                    "collections",
                    "indexing",
                    "filtering",
                    "searching",
                    "scheduling")

    filters = ["IFilter", "Xapian", "Text"]
    
    formats = ["txt", "doc", "rtf", "html", "pdf", "xsl", "ppt"]
    formats.sort()

    default_filter = filters[0] if os.name == 'nt' else filters[2]
    
    filter_settings = dict( (f, default_filter) for f in formats)
    if os.name != 'nt':
        filter_settings['html'] = 'Xapian'

    languages = [ ("none", "None"),
                  ("da", "Danish"),
                  ("nl", "Dutch"),
                  ("en", "English"),
                  ("fi", "Finnish"),
                  ("fr", "French"),
                  ("de", "German"),
                  ("it", "Italian"),
                  ("no", "Norwegian"),
                  ("pt", "Portuguese"),
                  ("ru", "Russian"),
                  ("es", "Spanish"),
                  ("sv", "Swedish")]
              
    return FlaxOptions(current_version,
                       formats, 
                       logger_names,
                       filters,
                       filter_settings,
                       languages)

# placeholder for global options object
options = None
