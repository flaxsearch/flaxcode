# Copyright (c) 2009 Lemur Consulting Ltd
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
r"""Database access utilities.

"""
__docformat__ = "restructuredtext en"

import os
import re
import sha
import unicodedata
import urllib
import wsgiwapi

def dbname_from_urlquoted(dbname_urlquoted):
    """Returns a database name (as a unicode string).

    Raises validation error if the supplied parameter is not a valid quoted
    utf8 string.

    """
    try:
        dbname = urllib.unquote(dbname_urlquoted).decode('utf8')
    except UnicodeDecodeError:
        raise wsgiwapi.ValidationError("Database name is not valid UTF8")
    return dbname

spaceunderdash_re = re.compile('[\s_-]+')
alnumspace_re = re.compile('[^A-Za-z0-9 ]')
space_re = re.compile(' +')

def dbname_to_filename(dbname):
    """Convert a database name, as supplied in the URL string, to a filename.

    """
    namehash = sha.sha(dbname).hexdigest()[:20]
    normname = unicodedata.normalize('NFKD', dbname).encode('ascii', 'ignore')
    normname = spaceunderdash_re.sub(' ', normname).strip()
    normname = alnumspace_re.sub('', normname)
    normname = space_re.sub('_', normname).lower()[:15]
    return normname + '__' + namehash

def dbpath_from_urlquoted(dbs_path, dbname_urlquoted):
    """Get the path for a database given the urlquoted database name.

    """
    filename = dbname_to_filename(dbname_from_urlquoted(dbname_urlquoted))
    return os.path.join(dbs_path, filename)
