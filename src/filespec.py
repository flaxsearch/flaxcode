import os
import stat
import datetime

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

    def __init__(self, paths=None, exclusions=None, earliest=None, latest=None, oldest=None, youngest=None):

            self.paths = [os.abspath(p) for p in paths] if paths else []
            self.exclusions = exclusions if exclusions else []
            self.earliest = earliest
            self.latest = latest
            self.oldest = oldest
            self.youngest = youngest

    def files(self):
        """ generates the files defined by this FileSpec """
        for p in self.paths:
            for root, dir, files in os.walk(p):
                for f in files:
                    if self.included(f):
                        yield f

                dirs = filter(dirs, self.dirs_included)

    def included(self, f):
        """ is this file permitted?"""

        # is this file one of the permitted formats?
        if not any ((fnmatch.fnmatch(f, e) for e in self.formats)):
            return false
        # format is ok, are we with the permitted range of dates.
        mtime = datetime.datetime.fromtimestamp(os.stat(f)[stat.ST_MTIME])
        #TODO: factor out the call to now().
        age = datetime.now() - mtime

        # a little long-winded because we have to allow for some
        # properties being None. We could compile up a version of this
        # test each time one of the date related properties changes
        # since presumably that will happen much less often than we
        # actually use the test.
        return not self.exclusion(f) and \
               (self.earliest < mtime if self.earliest else True) and \
               (mtime < self.latest if self.latest else True) and \
               (self.oldest < age if self.oldest else True) and \
               (age < self.youngest if self.youngest else True)


    def exclusion(self, f):
        return not any ((fnmatch.fnmatch(f, e) for e in self.exclusions))
               
