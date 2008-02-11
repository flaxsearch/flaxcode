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

import os

import collection_list
import flaxpaths
import flaxlog

# The current configuration file version - update this each time things change
# incompatibly.
current_version = 12

class FlaxOptions(object):
    """Global options for Flax.

    """

    # The formats which we support.
    formats = sorted(["txt", "doc", "rtf", "html", "htm", "pdf", "xls", "ppt",])

    # A list of the available languages - the first item in each tuple is the
    # internal name, and the second item in the tuple is the (english) display
    # name.
    # FIXME - this should probably be read from xappy, which in turn should
    # read it from Xapian, to ensure that the list is up-to-date with the
    # version of Xapian in use.
    languages = (("none", "None"),
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
                 ("sv", "Swedish")
                )

    def __init__(self):
        self.collections = None

    def initialised(self):
        """Check if this options object has been initialised."""
        return self.collections is not None

    def to_dict(self):
        """Convert the settings to a dictionary.

        Only those settings which should be preserved across invocations, and
        versions, of Flax will be placed in the dictionary.

        Returns the dictionary of settings.

        """
        return {
            # The version of this configuration.
            'version': current_version,

            # The collections in use.
            'collections': self.collections.to_dict(),

            # These are the default filter settings.
            'filter_settings': self.filter_settings,
        }

    def from_dict(self, settings):
        """Update the settings from a dictionary.

        """
        if self.collections is None:
            self.collections = collection_list.CollectionList()
        self.collections.from_dict(settings['collections'])
        self.filter_settings = settings['filter_settings']

    def set_to_defaults(self):
        """Set the settings to default values.

        """
        if os.name == 'nt':
            default_filter = 'IFilter'
        else:
            default_filter = 'Text'
        filter_settings = dict( (f, default_filter) for f in FlaxOptions.formats)
        filter_settings['html'] = filter_settings['htm'] = 'Xapian'
        filter_settings['txt'] = 'Text'

        self.filter_settings = filter_settings
        self.collections = collection_list.CollectionList()

    def _set_log_settings(self, vals):
        pass
#       FIXME
#        new_levels = {}
#        for name in self.logger_names:
#            if name in vals:
#                new_levels[name] = vals[name]
#        if "default" in vals:
#            new_levels[""] = vals["default"]
#
#        lq = logclient.LogConf(flaxpaths.paths.logconf_path)
#        lq.set_levels(new_levels)
#        
#        # This is here so that the web page that people see after
#        # setting a new option reflects the change that they've just
#        # made. See
#        # http://code.google.com/p/flaxcode/issues/detail?id=55
#        lq.update_log_config()

    def _get_log_settings(self):
        return None # FIXME
#        # is .level part of the public api for logger objects?
#        # FIXME - check
#        return dict((name, logging.getLevelName(logging.getLogger(name).level)) for name in self.logger_names)

#    log_settings = property(fset=_set_log_settings, fget=_get_log_settings, doc=
#        """A dictionary mapping log event names to log levels.
#
#        It is permitted for the dictionary to contain names that do not name a log
#        event, such will be silently ignored.
#
#        """)

    @property
    def log_levels(self):
        """The list of supported logging levels.

        """
        return ('NOTSET', 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')

# Global options object
options = FlaxOptions()
