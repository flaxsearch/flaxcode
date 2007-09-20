import os
import stat
import datetime
import fnmatch

import util

class FileSpec(object):
    """Filespaec: define a set of files and then do things with them.

    Paths - a set of absolute paths. If a path is a directory then in
    stands for all the files (recursively) contained within it.

    formats - filetypes to be included.

    Exclusions - a set of patterns removing files or paths.

    earliest:datetime - files before this date are excluded

    latest:datetime - files after this date are excluded

    oldest:timedelta - a duration, when an operation is performed
    anything modified more than this amount of time ago is excluded.

    youngest:timedelta -a duration: when an opertation is performed
    anything modified less than this amount of time ago is excluded.

    Note that Oldest and Youngest are relative to some event
    (anything that involves computing the set of files for the
    FileSpec) whereas Earliest and Latest are absolute dates.
"""

    strptime_format = "%d/%m/%y %H:%M:%S"

    def update(self, paths=None, earliest=None, latest=None,
               oldest=None, youngest=None, formats = [], **kwargs):

        self.paths = [paths] if isinstance(paths, str) else paths
        self.earliest = earliest
        self.latest = latest
        self.oldest = oldest
        self.youngest = youngest
        self.formats = [formats] if isinstance(formats, str) else formats

    def files(self):
        """ generates the files defined by this FileSpec """
        for p in self.paths:
            for root, dirs, files in os.walk(p):
                for f in files:
                    fname = os.path.join(root, f)
                    if self.included(fname):
                        yield fname

    def _get_earliest(self):
        return self._earliest

    def _set_earliest(self, date):
        self._earliest = self._process_datetime(date)

    earliest = property(fget = _get_earliest, fset = _set_earliest)

    def _get_latest(self):
        return self._latest

    def _set_latest(self, date):
        self._latest = self._process_datetime(date)

    latest = property(fget = _get_latest, fset = _set_latest)

    def _get_youngest(self):
        return self._youngest

    def _set_youngest(self, val):
        self._youngest = self._process_timedelta(val)

    youngest = property(fget = _get_youngest, fset = _set_youngest)

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


    def _process_datetime(self, date):
        if not date:
            return None
        elif isinstance(date,  str):
            try:
                return datetime.datetime.strptime(date, self.strptime_format)
            except ValueError:
                return None
        elif isinstance(date, datetime.datetime):
            return date
        else:
            raise ValueError("Value must be None, a string, or a datetime.datetime")

                


    
    def included(self, f):
        """ is the file name by f included in this spec? """

        # is this file one of the permitted formats?
        if not any ((fnmatch.fnmatch(f, '*.'+e) for e in self.formats)):
            return False

        # format is ok, are we with the permitted range of dates.
        mtime = datetime.datetime.fromtimestamp(os.stat(f)[stat.ST_MTIME])
        #TODO: factor out the call to now().
        age = datetime.datetime.now() - mtime

        return (self.earliest < mtime if self.earliest else True) and \
               (mtime < self.latest if self.latest else True) and \
               (self.oldest < age if self.oldest else True) and \
               (age < self.youngest if self.youngest else True)

               
