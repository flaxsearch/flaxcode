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
"""Version information.

"""
__docformat__ = "restructuredtext en"

import re
import getsvnrev

# The various parts of the version number
_version_number_major = 1
_version_number_minor = 0
_version_number_revision = 0

# Set to True if this is an official release.
_is_release = True

def _calc_svn_revision():
    """Calculate the SVN revision part of the version number.

    This is performed once on initial import of the module, and shouldn't need
    to be performed again.

    """
    if _is_release:
        return None

    # First, try getting the svn revision from the working directory.
    # Will raise a RevisionException if the working directory isn't an SVN
    # repository, or if the svn command line tools can't be found, or if some
    # error occurs while running the tools.
    try:
        rev = getsvnrev.get_svn_rev()
    except getsvnrev.RevisionException, e:
        pass
    else:
        return rev

    # Next, see if we have a generated svnrevision module, which will contain a
    # cached value.  (This method is used for for frozen executables, and
    # snapshot builds.)
    try:
        import svnrevision
        return svnrevision.svn_revision
    except ImportError, e:
        pass

    return "unknown"

# The svn revision in use.
_svn_revision = _calc_svn_revision()


def get_major():
    "Get the major version number." 
    return _version_number_major

def get_minor():
    "Get the minor version number." 
    return _version_number_minor

def get_revision():
    "Get the revision version number." 
    return _version_number_revision

def get_svn():
    """Get the SVN part of the version number.

    If this is an official release, this will be None.  Otherwise, it will be
    an SVN revision number, or "svn" if the SVN revision number couldn't be
    obtained (eg, the sources weren't obtained from SVN).

    Note that the revision may not be a pure number - it may include various
    strings to indicate that a branch, or a third-party repository, is being
    used.

    """
    return _svn_revision

def get_version_string():
    '''Get a string representing the version number.
    
    This will be in major.minor.revision or major.minor.revision.svn format.

    '''
    if _svn_revision is None:
        return '%d.%d.%d' % (_version_number_major,
                             _version_number_minor,
                             _version_number_revision)
    else:
        return '%d.%d.%d.%s' % (_version_number_major,
                                _version_number_minor,
                                _version_number_revision,
                                _svn_revision)
