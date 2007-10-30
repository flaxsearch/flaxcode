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

# The various parts of the version number
_version_number_major = 0
_version_number_minor = 9
_version_number_revision = 0

# Set to True if this is an official release.
_is_release = False

# Automatically updated to the SVN version this was checked out at.
_svn_revision = '$LastChangedRevision$'

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
    """Get the svn part of the version number.

    If this is an official release, this will be None.  Otherwise, it will be
    an SVN revision number, or "svn" if the SVN revision number couldn't be
    obtained (eg, the sources weren't obtained from SVN).

    """
    if _is_release:
        return None

    svnrev = re.search('[0-9]+', _svn_revision)
    if svnrev:
        svnrev = svnrev.group(0)
    else:
        svnrev = 'svn'
    return svnrev

def get_version_string():
    '''Get a string representing the version number.
    
    This will be in major.minor.revision or major.minor.revision.svn format.

    '''
    svnrev = get_svn()
    if svnrev is None:
        return '%d.%d.%d' % (_version_number_major,
                             _version_number_minor,
                             _version_number_revision)
    else:
        return '%d.%d.%d.%s' % (_version_number_major,
                                _version_number_minor,
                                _version_number_revision,
                                svnrev)
