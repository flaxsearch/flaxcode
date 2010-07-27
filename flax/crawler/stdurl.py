# Copyright (C) 2010 Lemur Consulting Ltd
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

""" Module including a standard URL class.
"""

from urlparse import urljoin, urlsplit


def stdurl(raw_url):
    """ Convert the argument to a StdURL.
    """
    if raw_url is None or raw_url == "":
        return None
    return StdURL(raw_url)


class StdURL (object):
    """Class representing a URL, the scheme of which is assumed to be HTTP.
    """

    def __init__(self, url, parent=None):
        """ Create a StdURL instance for the given URL.
        
            If parent is specified, then the URL is resolved relative to it.
        """
        if parent is not None:
            # resolve the url relative to the parent
            if isinstance(parent, StdURL):
                parent = str(parent)
            if isinstance(url, StdURL):
                url = str(url)
            url = urljoin(parent, url)
        # in case a StdURL is passed as the url argument (copy)
        if isinstance(url, StdURL):
            parts = url
        else:
            parts = urlsplit(url.strip())
        # pull out most parts from urlsplit
        self.scheme = parts.scheme
        self.hostname = parts.hostname
        self.port = parts.port
        self.netloc = parts.netloc
        self.path = parts.path
        self.query = parts.query
        # compute some extra properties based on above
        if self.path.find(".") == -1:
            self.extension = ""
        else:
            self.extension = self.path.split(".")[-1]
        query_str = "?{0}".format(self.query) if self.query else ""
        self.selector = "{0}{1}".format(self.path, query_str)

    def __eq__(self, other):
        """ Two StdURL instances are equal if they have the same scheme, host,
            port, path and query.
        """
        if other is None:
            return False
        return self.scheme == other.scheme and self.netloc == other.netloc \
               and self.selector == other.selector

    def __ne__(self, other):
        """ Two StdURL instances are unequal if they differ in scheme, host,
            port, path or query.
        """
        if other is None:
            return True
        return self.scheme != other.scheme or self.netloc != other.netloc \
               or self.selector != other.selector

    def __hash__(self):
        """ Returns a suitable hash value for the StdURL.
        """
        return hash(str(self))

    def __str__(self):
        """ Ignore any URL fragment (#foo) for the string representation.
        """
        return "{0}://{1}{2}".format(self.scheme, self.netloc, self.selector)


if __name__ == "__main__":
    url1 = StdURL("http://www.google.com")
    url2 = StdURL("http://www.google.com")
    url3 = StdURL("http://www.google.co.uk")
    assert url1.scheme == "http"
    assert url1 == url2
    assert not url1 != url2
    assert url2 != url3
    assert not url2 == url3
    assert url1 != None
    s = set([url1, url2, url3])
    assert len(s) == 2
    url4 = StdURL("http://www.abc.com/")
    assert StdURL("mailto:abc@foo.com", url4).scheme == "mailto"
    assert StdURL("foo.html", url4) == StdURL("http://www.abc.com/foo.html")
    assert StdURL("http://foo", url4) == StdURL("http://foo")
    print "TEST PASSED"

