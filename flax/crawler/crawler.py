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

""" Module for web crawling.
"""

from urllib2 import urlopen, Request, URLError, HTTPError
from httplib import IncompleteRead
from robotparser import RobotFileParser
from time import time, sleep
from hashlib import md5
from random import randint
from re import compile as re_compile, IGNORECASE
from new import instancemethod
from threading import Thread, Lock, current_thread
from inspect import currentframe
from sys import exc_info, exc_clear

from stdurl import StdURL


silent = True # if False, output debug to stdout
user_agent = "FlaxBot/0.1 (see http://www.flax.co.uk/)"
default_delay = 4 # default time between requests for a domain
http_threads = 10 # number of crawler threads


class CrawlerError (Exception):
    """ Base class for errors encountered whilst crawling.
    """
    pass


class NoRobots (CrawlerError):
    """ Exception raised when no robots.txt has been fetched for a domain.
    """
    pass
     

class URLNotAllowed (CrawlerError):
    """ Exception raised when a URL is disallowed by robots.txt.
    """
    pass


class URLNotFollowed (CrawlerError):
    """ Exception raised when a URL is followed (downloaded).
    """
    pass


class DuplicateURL (CrawlerError):
    """ Exception raised when a duplicate URL is encountered.
    """
    pass
    

class DuplicateResource (CrawlerError):
    """ Exception raised when a duplicate resource is detected.
    """
    pass


class NotHandled (CrawlerError):
    """ Exception raised when a parser can not handle a resource.
    """
    pass


class DefaultDumper (object):
    """ Default implementation of a dumper, which maintains a count of dumped
        resources and the total number of characters.
        
        If the attribute api_lock is a Lock, calls to the API are synchronized.
    """
    
    api_lock = Lock()

    def __init__(self):
        self.count = 0
        self.chars = 0

    def dump_resource(self, resource):
        """ Dump a resource.
        """
        self.count += 1
        self.chars += len(resource.content)


class DefaultURLPool (object):
    """ Default implementation of a URL pool, maintaining URLs in memory.
        Also maintains a dictionary of URL to error encountered.
        
        If the attribute api_lock is a Lock, calls to the API are synchronized.
    """
    
    api_lock = Lock()
        
    def __init__(self):
        self._urls = list()
        self._seen = set()
        self._robots = list()
        self.repeat_count = 0
        self.link_count = 0
        self.redirect_count = 0
        
    def add_url(self, url):
        """ Add a StdURL to the pool.
        """
        self._urls.append(url)
        self._seen.add(url)
        robots_url = StdURL("http://{0}/robots.txt".format(url.netloc))
        if robots_url not in self._seen:
            self._robots.append(robots_url)
            self._seen.add(robots_url)
        
    def add_link(self, source, target):
        """ Add a link between the source StdURL and the target StdURL. Note
            that add_url is called for the target later if it is to be added to
            the pool of URLs.
        """
        assert source in self._seen
        assert target is not None
        self.link_count += 1

    def add_redirect(self, source, target):
        """ Add a redirect from the source StdURL to the target StdURL.
        """
        assert source in self._seen
        assert target is not None
        self.redirect_count += 1

    def check_url(self, url):
        """ If the URL pool has seen the specified StdURL, raise DuplicateURL.
        """
        if url in self._seen:
            self.repeat_count += 1
            raise DuplicateURL()

    def next_url(self):
        """ Return a StdURL from the to-do collection. If none are left,
            return None.
        """
        if len(self._robots) > 0:
            url = self._robots[0]
            self._robots.remove(url)
            return url
        if len(self._urls) == 0:
            return None
        url = self._urls[randint(0, len(self._urls) - 1)]
        self._urls.remove(url)
        return url


class DefaultErrorHandler (object):
    """ Default implementation of an error handler.
        
        If the attribute api_lock is a Lock, calls to the API are synchronized.
    """
    
    api_lock = Lock()

    def error(self, url, e):
        """ Record the error, e, against the specified StdURL.
        """
        pass


class DefaultFollowDecider (object):
    """ Default implementation of a follow decider (for deciding which URLs to
        download).
        
        If the attribute api_lock is a Lock, calls to the API are synchronized.
    """
    
    api_lock = Lock()
    
    def __init__(self, content_type_re, same_domain=False):
        """ Only follow resources with a content type matching the regexp, and
            if same_domain is True, only follow link targets on the same domain
            as the original URL.
        """
        self._re = re_compile(content_type_re)
        self._same_domain = same_domain

    def follow_resource(self, resource):
        """ If the resource should not be followed, raise URLNotFollowed. This
            is called twice, once after the HEAD request (when resource.content
            is None) and again after the GET request.
        """
        if resource.content is not None:
            return
        if not self._re.match(resource.content_type()):
            raise URLNotFollowed()

    def follow_url(self, resource, target):
        """ If the specified URL (an instance of StdURL) should not be
            followed, raise URLNotFollowed.
        """
        if self._same_domain and resource.origin_url.netloc != target.netloc:
            raise URLNotFollowed()


class DefaultDuplicateDetector (object):
    """ Default implementation of a duplicate detector, using an in-memory
        set of ETags and content hashes.
        
        If the attribute api_lock is a Lock, calls to the API are synchronized.
    """
    
    api_lock = Lock()
    
    def __init__(self):
        self.etags = set()
        self.hash_set = set()
        
    def duplicate_resource(self, resource):
        """ Check a web resource for duplication. This will be called twice,
            once after the HEAD request (when resource.content is None) and
            again after the GET request.
        """
        if resource.content is None:
            # check the ETag, if there is one
            etag = resource.headers.get("ETag")
            if etag is not None:
                if etag in self.etags:
                    raise DuplicateResource()
                self.etags.add(etag)
            return
        # now check and update the hash set
        hasher = md5()
        hasher.update(resource.content)
        value = hasher.digest()
        if value in self.hash_set:
            raise DuplicateResource()
        self.hash_set.add(value)


class DefaultHtmlParser (object):
    """ Default implementation of an HTML link parser, using a (not very
        sophisticated) regular expression.
        
        If the attribute api_lock is a Lock, calls to the API are synchronized.
    """
    
    content_types = ("text/html", "application/xhtml+xml")
    
    def __init__(self):
        # note that {0}, {1} are not part of the regular expression
        re = "<\s*{0}\s+{1}\s*=\s*(\"[^\"]+\"|'[^']+')\s*/?>"
        self._a = re_compile(re.format("a", "href"), IGNORECASE)
        self._img = re_compile(re.format("img", "src"), IGNORECASE)
        meta = "<\s*meta\s+name\s*=\s*(\"robots\"|'robots')\s+" \
               "content\s*=\s*(\"[^\"]+\"|'[^']+')\s*/?>"
        self._meta = re_compile(meta, IGNORECASE)
        
    def parse_resource(self, resource):
        """ Yield target URLs from the given HTML content, and set noindex and
            nofollow on the resource if necessary. Raise NotHandled if the
            resource can not be handled by this parser.
        """
        if resource.content_type() not in DefaultHtmlParser.content_types:
            raise NotHandled()
        meta = self._meta.findall(resource.content)
        if len(meta) > 0:
            content = meta[0][1].lower()
            if "noindex" in content:
                resource.noindex = True
            if "nofollow" in content:
                resource.nofollow = True
        for url in self._a.findall(resource.content) + \
                   self._img.findall(resource.content):
            yield url.strip("\"'")
        
            
class DefaultThrottle (object):
    """ Default implementation of a throttle, maintaining a in-memory map from
        domain last fetch time.
        
        If the attribute api_lock is a Lock, calls to the API are synchronized.
    """
    
    api_lock = Lock()
    
    def __init__(self):
        self.hosts = dict()
        
    def last_time(self, netloc):
        """ Return the last time a request was made to the specified domain,
            and record that a request is being made now. Returns 0 if this is
            the first request.
        """
        t = self.hosts.get(netloc)
        self.hosts[netloc] = time()
        return t or 0


class DefaultRobotManager (object):
    """ Default implementation of a manager for robots.txt information.
        Maintains an in-memory map from netloc to an instance of
        RobotExclusionRulesParser.
        
        If the attribute api_lock is a Lock, calls to the API are synchronized.
    """
    
    api_lock = Lock()
    
    def __init__(self):
        self._robots = dict()

    def parse_robots(self, netloc, content):
        """ Parse the given robots.txt content and store against the given
            domain. If content is None, any URL will be allowed.
        """
        robot = RobotFileParser()
        if content is not None:
            robot.parse(content.split("\n"))
        self._robots[netloc] = robot
        
    def check_robots(self, url):
        """ If no attempt has yet been made to fetch robots.txt for the domain
            of the specified StdURL, raise NoRobots. Otherwise, if access to
            the URL is not allowed according to the stored robots.txt, raise
            URLNotAllowed. Otherwise, return the crawl delay required by
            robots.txt, or None if not specified.
        """
        robot = self._robots.get(url.netloc)
        if robot is None:
            raise NoRobots()
        if not robot.can_fetch(user_agent, url.path):
            raise URLNotAllowed()
        return default_delay


dump = DefaultDumper()
pool = DefaultURLPool()
follow = DefaultFollowDecider(".*")
duplicate = DefaultDuplicateDetector()
parsers = (DefaultHtmlParser(), )
throttle = DefaultThrottle()
robots = DefaultRobotManager()
error = DefaultErrorHandler()


def _sync(arg, *args):
    """ Synchronize calls to an instancemethod (defaults to __call__ if an
        object is passed) using the api_lock attribute of the bound object (or
        passed object). If api_lock is not set, no synchronization is done.
    """
    if isinstance(arg, instancemethod):
        obj = arg.im_self
        fn = arg
    else:
        obj = arg
        fn = arg.__call__
    lock = getattr(obj, "api_lock", None)
    if lock is not None:
        lock.acquire()
    try:
        return fn(*args)
    finally:
        if lock is not None:
            lock.release()


class HTTPResource (object):
    """ Class for storing the results of a successful HTTP GET.
    """
    
    def __init__(self, origin_url, url, headers):
        self.origin_url = origin_url
        self.url = url
        self.headers = headers
        self.content = None
        self.noindex = False
        self.nofollow = False

    def content_type(self):
        """ Return the primary content type from the Content-Type header.
        """
        content_type = self.headers.get("Content-Type")
        if content_type is None:
            return None
        return content_type.split(";")[0]

    def check(self):
        """ Check for duplicate (redirected) URL and content, and whether to
            follow (raises exceptions if not).
        """
        if self.url != self.origin_url:
            _sync(pool.check_url, self.url)
        _sync(duplicate.duplicate_resource, self)
        _sync(follow.follow_resource, self)


class _Courier (Request):
    """ Class for using urllib2 to request web page content via HTTP.
    """

    def __init__(self, url):
        """ Initialise the courier for the given page.
        """
        Request.__init__(self, str(url).replace(" ", "%20"))
        self._method = None
        self.add_header("User-Agent", user_agent)
    
    def get_method(self):
        """ Specifies the method used by urllib2 when making an HTTP request.
        """
        return self._method

    def fetch(self, method):
        """ Send a request of the specified type (HEAD, GET) for the given URL.
            Returns the HTTP response.
            
            Can raise URLError, HTTPError or IncompleteRead.
        """
        self._method = method
        return urlopen(self)


class CrawlerThread (Thread):
    """ Worker thread for crawling URLs.
    """
    
    def __init__(self):
        Thread.__init__(self, target=_crawl)
        self.waiter = None
        self._lock = Lock()
        self._lock.acquire()
                
    def wait(self):
        """ Make the thread wait for notification.
        """
        self._lock.acquire()
        
    def notify(self):
        """ Wake the thread.
        """
        self._lock.release()


def _crawl():
    """ Crawl URLs obtained from _iter_urls(), scraping and adding to the URL
        pool we go.
    """
    for url in _iter_urls():
        _debug("Crawling", url)
        try:
            if url.path == '/robots.txt':
                _get_robots(url)
            else:
                _get_url(url)
        except (CrawlerError, URLError, IncompleteRead) as e:
            _debug(url)
            _sync(error.error, url, e)
        except:
            # error is not lost - see _debug()
            stop()

def _get_robots(url):
    """ Fetch a robots.txt URL and send the content to the robots module.
    """
    # initialise the throttle for this domain
    _sync(throttle.last_time, url.netloc)
    # make a GET request for robots.txt
    _debug("HTTP GET", url)
    courier = _Courier(url)
    try:
        response = courier.fetch("GET")
    except HTTPError as e:
        if e.code == 404:
            content = None
        else:
            raise
    else:
        content = response.read()
        response.close()
    # send content to robots for parsing
    _sync(robots.parse_robots, url.netloc, content)
        
def _get_url(url):
    """ Fetch a URL. Note that this is synchronized by the engine such that
        it will only be called for each domain (url.netloc) once at a time.
    """
    # check robots.txt
    delay = _sync(robots.check_robots, url) or default_delay
    # hit the throttle and wait if necessary
    t = _sync(throttle.last_time, url.netloc)
    wait = t + delay - time()
    if wait > 0:
        _debug("Sleep for", wait)
        sleep(wait)
    _sync(throttle.last_time, url.netloc)
    # make a HEAD request to check the headers
    courier = _Courier(url)
    _debug("HTTP HEAD", url)
    response = courier.fetch("HEAD")
    resource = HTTPResource(url, StdURL(response.url), response.headers)
    # check for a redirect
    if resource.url != resource.origin_url:
        _sync(pool.add_redirect, resource.origin_url, resource.url)
    # check whether to reject on (redirected) URL, headers or content type
    resource.check()
    # make a GET request for the resource, and replace details just in case
    _debug("HTTP GET", url)
    response = courier.fetch("GET")
    resource.url = StdURL(response.url)
    resource.headers = response.headers
    resource.content = response.read()
    response.close()
    # check whether to reject on (redirected) URL, headers or content
    resource.check()
    # attempt to parse the content
    parent = StdURL(resource.url)
    for parser in parsers:
        try:
            for rel_url in _sync(parser.parse_resource, resource):
                target = StdURL(rel_url, parent)
                try:
                    if target.scheme != parent.scheme:
                        raise URLNotFollowed()
                except URLNotFollowed:
                    _debug(target)
                    continue
                _sync(pool.add_link, url, target)
                try:
                    _sync(pool.check_url, target)
                except DuplicateURL:
                    _debug(target)
                    continue
                try:
                    _sync(follow.follow_url, resource, target)
                except URLNotFollowed:
                    _debug(target)
                else:
                    if not resource.nofollow:
                        _sync(pool.add_url, target)
        except NotHandled:
            exc_clear()
        else:
            break
    # dump the resource (if allowed)
    if not resource.noindex:
        _debug("Dump", url, resource.content_type())
        _sync(dump.dump_resource, resource)

_debug_lock = Lock()
def _debug(*args):
    """ Output a log line using the given arguments, including exception
        details if called in the context of an 'except' clause.
    """
    ty, e, tb = exc_info()
    if (e is None or isinstance(e, CrawlerError)) and silent:
        return
    if ty is not None:
        while tb.tb_next is not None:
            tb = tb.tb_next
        f = tb.tb_frame
        lineno = tb.tb_lineno
        exc_clear()
    else:
        frame = currentframe()
        f = frame.f_back
        lineno = f.f_lineno
    _debug_lock.acquire()
    print round(time() - t0, 1), current_thread().name,
    print "{0}:{1} {2}".format(f.f_code.co_filename, lineno, f.f_code.co_name),
    print "|",
    if e is not None:
        print e.__class__.__name__,
        if len(str(e)) > 0:
            print "({0})".format(str(e)),
    print " ".join([str(x) for x in args])
    _debug_lock.release()


_threads = list()
_waiters = set() # locks for blocking workers on the next URL
_lock = Lock() # for locking waiter and domain map code
_domain_map = dict() # for looking up threads working on a domain
_halt = False # if a thread sets this to True, stop everything gracefully

t0 = 0

def start():
    """ Start the crawler, returning when all crawler threads have terminated.
    """
    global t0
    t0 = time()
    for _ in xrange(http_threads):
        _threads.append(CrawlerThread())
    for thread in _threads:
        thread.start()
    while len(_threads) > 0:
        thread = _threads[0]
        thread.join()
        _threads.remove(thread)

def stop():
    """ Gracefully stop the crawler prematurely. Crawler threads will still
        operate until all URLs handed out by the URL pool have been handled.
    """
    global _halt
    _halt = True
    _debug("Stop")

def _wait():
    """ Cause the current thread to wait, or if all threads are waiting notify
        them, so that the engine can halt gracefully.
    """
    waiter = Lock()
    waiter.acquire()
    _waiters.add(waiter)
    if len(_waiters) == len(_threads):
        for waiter in _waiters:
            waiter.release()
    else:
        _lock.release()
        waiter.acquire()
        _lock.acquire()

def _iter_urls():
    """ Yield URLs obtained from the URL Pool module, causing threads to wait
        when no more URLs are available, and wait on threads fetching a URL
        from the same domain.
    """
    # workers call this function; _lock ensures only one at a time
    _lock.acquire()
    while len(_waiters) < len(_threads):
        _lock.release()
        url = _sync(pool.next_url) if not _halt else None
        _lock.acquire()
        if url is None:
            _wait() # wait for a URL to be ready
            continue
        if len(_waiters) > 0:
            _waiters.pop().release()
        # check domain map for worker threads already working the domain
        if url.netloc in _domain_map:
            # add me as a waiter for the working thread, and make me wait
            thread = _domain_map[url.netloc]
            while thread.waiter is not None:
                thread = thread.waiter
            thread.waiter = current_thread()
            _debug("Add as waiter for", thread.name)
            _lock.release()
            current_thread().wait()
            _lock.acquire()
        else:
            # add me to the domain map
            _domain_map[url.netloc] = current_thread()
        _lock.release()
        yield url
        _lock.acquire()
        # remove me from the domain map, and wake and promote a waiter
        if current_thread().waiter is not None:
            _domain_map[url.netloc] = current_thread().waiter
            _debug("Wake", current_thread().waiter.name)
            current_thread().waiter.notify()
            current_thread().waiter = None
        else:
            del _domain_map[url.netloc]
    _lock.release()

if __name__ == "__main__":
    from sys import argv
    
    if "-v" in argv[1:]:
        silent = False
    if "-q" in argv[1:]:
        default_delay = 0

    class DomainFollowDecider (DefaultFollowDecider):
        """ Test implementation.
        """

        def __init__(self, content_type_re, domain_set):
            DefaultFollowDecider.__init__(self, content_type_re)
            self.domain_set = domain_set
            
        def follow_resource(self, resource):
            """ Do not follow URLs that are outside the set of allowed domains.
            """
            DefaultFollowDecider.follow_resource(self, resource)
            if resource.origin_url.netloc not in self.domain_set:
                raise URLNotFollowed()

    class TestErrorHandler (DefaultErrorHandler):
        """ Test implementation.
        """
        
        api_lock = Lock()
            
        def __init__(self):
            DefaultErrorHandler.__init__(self)
            self.count = 0
            self.by_type = dict()

        def error(self, url, e):
            """ Add the URL to a set held against the error type.
            """
            self.count += 1
            if type(e) not in self.by_type:
                self.by_type[type(e)] = set()
            self.by_type[type(e)].add(url)
            
        def __str__(self):
            """ Print errors to stdout.
            """
            s = "{0} logged errors\n".format(self.count)
            for e_type, e_set in self.by_type.iteritems():
                for url in e_set:
                    s += "{0} {1}\n".format(e_type.__name__, url)
            return s

    follow = DomainFollowDecider("^text/html$|^image/.*",
                                 set(["test", "doesnotexist.net.uk"]))
    error = TestErrorHandler()
    pool.add_url(StdURL("http://test/"))

    start()

    if not silent:
        print
        print error
        
    for u, y in (("http://test/does_not_exist.html", HTTPError),
                 ("http://doesnotexist.net.uk/page.html", NoRobots),
                 ("http://test/empty.mp3", URLNotFollowed),
                 ("http://test/test.jpg", URLNotAllowed)):
        assert StdURL(u) in error.by_type[y]
    assert dump.count == 12
    assert error.count == 10
    assert pool.repeat_count == 3
    assert pool.link_count == 23
    assert pool.redirect_count == 1
    assert len(duplicate.etags) == 8
    assert len(duplicate.hash_set) == 13
    assert dump.chars == 542791
    # test throttle
    count = dump.count + error.count - pool.repeat_count
    print time() - t0, default_delay * count
    assert time() - t0 >= default_delay * count
    print "Test passed"

