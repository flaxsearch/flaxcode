import os
import stat
import datetime
import fnmatch

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

    def update(self, paths=None, exclusions=None, earliest=None,
               latest=None, oldest=None, youngest=None, formats = None, **kwargs):

        self.paths = [paths] if type(paths) is str else paths
        self.exclusions = exclusions if exclusions else []
        self.earliest = earliest
        self.latest = latest
        self.oldest = oldest
        self.youngest = youngest
        self.formats = ['*.txt'] if formats is None else formats

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

    def _process_datetime(self, date):
        if date is None:
            return None
        elif type(date) is str:
            return datetime.datetime.strptime(date, self.strptime_format)
        elif type(date) is datetime.datetime:
            return date
        else:
            raise ValueError("Value must be a None, a string, or a datetime.datetime")

    def _get_latest(self):
        return self._latest

    def _set_latest(self, date):
        self._latest = self._process_datetime(date)

    latest = property(fget = _get_latest, fset = _set_latest)
            
    
    def included(self, f):
        """ is this file permitted?"""

        # is this file one of the permitted formats?
        if not any ((fnmatch.fnmatch(f, '*.'+e) for e in self.formats)):
            return False

        return True        # temporary 

        # format is ok, are we with the permitted range of dates.
        mtime = datetime.datetime.fromtimestamp(os.stat(f)[stat.ST_MTIME])
        #TODO: factor out the call to now().
        age = datetime.datetime.now() - mtime

        #TODO: refactor to benefit from short-ciruiting - leave like
        #this for debugging for now

        # a little long-winded because we have to allow for some
        # properties being None. We could compile up a version of this
        # test each time one of the date related properties changes
        # since presumably that will happen much less often than we
        # actually use the test.
        excluded = self.exclusion(f)
        not_early = (self.earliest < mtime if self.earliest else True)
        not_late = (mtime < self.latest if self.latest else True)
        not_old = (self.oldest < age if self.oldest else True)
        not_young = (age < self.youngest if self.youngest else True)

        return (not excluded) and not_early and not_late and not_old and not_young

    def exclusion(self, f):
        return any ((fnmatch.fnmatch(f, e) for e in self.exclusions))
               
