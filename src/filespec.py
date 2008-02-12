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
"""File specification - how to define a set of files.

"""
__docformat__ = "restructuredtext en"

import os
import stat
import datetime
import fnmatch

import flaxlog
import util

_log = flaxlog.getLogger('indexing')

class FileSpec(object):
    """Filespec: define a set of files and then do things with them.

    Paths - a set of absolute paths. If a path is a directory then in
    stands for all the files (recursively) contained within it.

    formats - filetypes to be included.

    oldest:timedelta - a duration, when an operation is performed
    anything modified more than this amount of time ago is excluded.

    """

    strptime_format = "%d/%m/%y %H:%M:%S"

    def update(self, paths=None,  oldest=None, formats = [], **kwargs):
        if paths == None:
            paths = []
        self.paths = [paths] if isinstance(paths, str) else paths
        self.oldest = oldest
        self.formats = util.listify(formats) if formats else []

    def files(self):
        """Returns an iterator over the files defined by this FileSpec."""

        def log_file_walked(f):
            _log.debug("Walked to file %s" % f)
        
        for p in self.paths:
            # Test "p + os.path.sep" here instead of just "p" here to fix a
            # problem on windows: NT shared directories, and windows drive
            # letters, don't return true for isdir unless followed by '\'.  See
            # http://code.google.com/p/flaxcode/issues/detail?id=167 for
            # details.
            if os.path.isdir(p + os.path.sep):
                for root, dirs, files in os.walk(p):
                    # Perhaps we want to warn here if any dirs are
                    # symlinks. os.walk will not traverse them. Don't do
                    # anything right now because we're targetting windows
                    # initially and therefore won't be hitting symlinks.
                    # Note that a symlink to a file will be included
                    # (assuming the file passes the other criteria for
                    # inclusion.)
                    for f in files:
                        fname = os.path.realpath(os.path.join(root, f))
                        log_file_walked(fname)
                        if os.path.exists(fname):
                            if self.included(fname):
                                yield fname
                        else:
                            _log.debug("Walked file %s, does not exist (dangling symlink?), skipping" % fname)
            elif os.path.isfile(p) and self.included(p):
                log_file_walked(p)
                yield p
            else:
                _log.error("File path %s is neither a directory or a file" % p )


    def _get_oldest(self):
        return self._oldest

    def _set_oldest(self, val):
        self._oldest = self._process_timedelta(val)

    oldest = property(fget = _get_oldest, fset = _set_oldest)

    def _process_timedelta(self, val):
        if not val:
            return None
        elif isinstance(val, str):
            # possibly we need to catch exceptions here - need to see
            # what gets raised
            return util.parse_timedelta(val)
        elif isinstance(val, datetime.timedelta):
            return val
        else:
            raise ValueError("Value must be None, a string or a datetime.timedelta")

    def included(self, fname):
        """ is the file name by fname included in this spec? """

        # is this file one of the permitted formats?
        if not any ((fnmatch.fnmatch(fname, '*.'+e) for e in self.formats)):
            _log.debug("File %s is not included in format list" % fname)
            return False

        # format is ok, are we with the permitted range of dates.
        mtime = datetime.datetime.fromtimestamp(os.path.getmtime(fname))

        age = datetime.datetime.now() - mtime
        if self.oldest and self.oldest >= age:
            _log.debug("File %s is too old" % fname)
            return False

        _log.debug("File %s is included" % fname)
        return True
