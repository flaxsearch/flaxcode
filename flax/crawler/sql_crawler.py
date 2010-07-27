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

""" Reference implementation of crawler, storing URLs in an SQL database (using
    sqlite3). Note (at least):
    
    * It's quite inefficient - SQL operations should be batched, results cached
    * No error handling - e.g. URLs are abandoned if they raise IncompleteRead
    * The default HTML parser doesn't understand meta redirects
"""

import crawler
from crawler import DefaultFollowDecider, DefaultHtmlParser, URLNotAllowed, \
                    NoRobots, DuplicateResource, DuplicateURL, URLNotFollowed,\
                    _debug
from robotparser import RobotFileParser
from time import time
from pickle import dumps, loads
from threading import Lock
from hashlib import md5
from sqlite3 import connect, Row, DatabaseError, Binary
from os import unlink
from os.path import isfile

from stdurl import StdURL


schema = """
CREATE TABLE content (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      url_id INTEGER NOT NULL UNIQUE,
                      content BLOB NOT NULL,
                      hash VARCHAR(32));
CREATE TABLE domain (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     netloc VARCHAR(256) NOT NULL UNIQUE,
                     robots BLOB,
                     time INTEGER DEFAULT 0);
CREATE TABLE header (id INTEGER PRIMARY KEY AUTOINCREMENT,
                     url_id INTEGER NOT NULL,
                     name VARCHAR(4096),
                     value VARCHAR(4096));
CREATE TABLE link (id INTEGER PRIMARY KEY AUTOINCREMENT,
                   source_id INTEGER NOT NULL,
                   target_id INTEGER NOT NULL,
                   count INTEGER NOT NULL);
CREATE TABLE redirect (id INTEGER PRIMARY KEY AUTOINCREMENT,
                       source_id INTEGER NOT NULL UNIQUE,
                       target_id INTEGER NOT NULL);
CREATE TABLE url (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  domain_id INTEGER NOT NULL,
                  url VARCHAR(4096) NOT NULL UNIQUE,
                  time INTEGER);
CREATE TABLE error (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url_id INTEGER NOT NULL UNIQUE,
                    type VARCHAR(64),
                    error VARCHAR(4096));
CREATE UNIQUE INDEX link_idx ON link (source_id, target_id);
CREATE UNIQUE INDEX redirect_idx ON redirect (source_id, target_id);
"""

class NoRow (Exception):
    """ Exception raised when a SELECT statement yield no rows.
    """
    
    def __init__(self, statement):
        Exception.__init__(self)
        self.statement = statement

    def __str__(self):
        return "No matching row found: {0}".format(self.statement)
           

class SQLImplementation (object):
    """ SQL implementation of sub-module APIs.
    """
    
    api_lock = Lock()

    def __init__(self, path):
        """ Open a connection to the MySQL database of company data.
        """
        self.db = connect(path, check_same_thread=False)
        self.db.row_factory = Row
        self.cursor = self.db.cursor()
        
    def execute(self, statement, *args):
        """ Execute the given SQL statement, substituting the remaining
            arguments into the statement. Returns the id of the inserted row,
            if any.
        """
        try:
            self.cursor.execute(statement, args)
            self.db.commit()
            return self.cursor.lastrowid
        except DatabaseError as e:
            _debug(statement)
            raise e
        
    def select(self, statement, *args):
        """ Execute the given SELECT SQL statement, substituting the remaining
            arguments into the statement. Returns the columns from the SELECT,
            or raises NoRow if no matching rows are found - but only the first
            result row.
        """
        try:
            self.cursor.execute(statement, args)
            result = self.cursor.fetchone()
            if result is None:
                raise NoRow(statement)
            if len(result) == 1:
                return result[0]
            return result
        except DatabaseError as e:
            _debug(statement)
            raise e
            
    def select_iter(self, statement, *args):
        """ Execute the given SELECT SQL statement, substituting the remaining
            arguments into the statement. Yields result rows as tuples.
        """
        try:
            self.cursor.execute(statement, args)
            for result in self.cursor.fetchall():
                yield result
        except DatabaseError as e:
            _debug(statement)
            raise e        
        
    def close(self):
        """ Close the database connection.
        """
        self.db.close()

    def initialise(self):
        """ Create SQL tables.
        """
        self.cursor.executescript(schema)

    def _select_url(self, url, select_time=False):
        """ Select a URL id from the database. If select_time, include the
            time column.
        """
        fs = "id" if not select_time else "id, time"
        return self.select("SELECT " + fs + " FROM url WHERE url=?", str(url))

    def _insert_url(self, url, t=None):
        """ Insert a URL into the database. If t is specified, set the URL time
            to that value. Returns the database id of the URL.
        """
        assert url.netloc != ""
        try:
            domain_id = self.select("SELECT id FROM domain WHERE netloc=?",
                                    url.netloc)
        except NoRow:
            domain_id = self.execute("INSERT INTO domain(netloc) VALUES (?)",
                                     url.netloc)
        return self.execute("INSERT INTO url(domain_id, url, time) " \
                            "VALUES (?, ?, ?)", domain_id, str(url), t)
          
    def dump_resource(self, resource):
        """ Dump the resource to the database. Check for redirects.
        """
        url_id = self._select_url(resource.url)
        for name, value in resource.headers.items():
            self.execute("INSERT INTO header(url_id, name, value) " \
                         "VALUES (?, ?, ?)", url_id, name, value)
        content = Binary(resource.content)
        self.execute("INSERT INTO content(url_id, content, hash) " \
                     "VALUES (?, ?, ?)", url_id, content, resource.hash)

    def add_url(self, url):
        """ Add a URL, referencing the domain (domain is created if it does not
            already exist).
        """
        try:
            url_id, t = self._select_url(url, select_time=True)
        except NoRow:
            self._insert_url(url, 0)
        else:
            if t is not None:
                raise DuplicateURL()
            self.execute("UPDATE url SET time=0 WHERE id=?", url_id)
    
    def add_link(self, source, target):
        """ Add a link by referencing the source and target URLs.
        """
        source_id = self._select_url(source)
        try:
            target_id = self._select_url(target)
        except NoRow:
            target_id = self._insert_url(target)
        try:
            link_id, count = self.select("SELECT id, count FROM link " \
                                         "WHERE source_id=? " \
                                         "AND target_id=?",
                                         source_id, target_id)
        except NoRow:
            self.execute("INSERT INTO link(source_id, target_id, count) " \
                         "VALUES (?, ?, 1)", source_id, target_id)
        else:
            self.execute("UPDATE link SET count=? WHERE id=?",
                         count + 1, link_id)
    
    def add_redirect(self, source, target):
        """ Add a redirect by referencing the source and target URLs.
        """
        orig_id = self._select_url(source)
        try:
            url_id = self._select_url(target)
        except NoRow:
            url_id = self._insert_url(target)
        self.execute("INSERT INTO redirect(source_id, target_id) " \
                     "VALUES (?, ?)", orig_id, url_id)
    
    def check_url(self, url):
        """ Check whether a URL has been seen by lookup into the URL table.
        """
        try:
            _, t = self._select_url(url, select_time=True)
            if t is not None:
                raise DuplicateURL()
        except NoRow:
            pass
    
    def next_url(self):
        """ Return a URL to fetch - try to return a URL referencing the domain
            with oldest 'time'. Update the 'time' on the returned URL with the
            current timestamp, and don't return URLs with a non-null time. If
            no URLs have been passed for domain of the URL, return the robots
            URL instead (recording on the domain the current timestamp).
        """
        global limit
        if limit is not None:
            if limit == 0:
                return None
            else:
                limit -= 1
        try:
            domain_id, url_id, url = self.select("SELECT domain_id, " \
                "url.id, url FROM domain, url WHERE url.domain_id=domain.id " \
                "AND url.time=0 ORDER BY domain.time LIMIT 1")
        except NoRow:
            return None
        url = StdURL(url)
        try:
            self.select("SELECT time FROM domain WHERE id=? AND time > 0",
                        domain_id)
        except NoRow:
            url = StdURL("http://{0}/robots.txt".format(url.netloc))
            self.execute("UPDATE domain SET time=? WHERE id=?",
                         int(time()), domain_id)
        else:
            self.execute("UPDATE url SET time=? WHERE id=?",
                         int(time()), url_id)
        return url

    def error(self, url, e):
        """ Record the error against the URL.
        """
        url_id = self._select_url(url)
        self.execute("INSERT INTO error(url_id, type, error) VALUES (?, ?, ?)",
                     url_id, e.__class__.__name__, str(e))
        
    def duplicate_resource(self, resource):
        """ Check a web resource for duplication.
        """
        if resource.content is None:
            # check the ETag, if there is one
            etag = resource.headers.get("ETag")
            if etag is not None:
                try:
                    self.select("SELECT id FROM header WHERE name=? " \
                                "AND value=?", "ETag", etag)
                    raise DuplicateResource()
                except NoRow:
                    pass
            return
        # check the hash
        hasher = md5()
        hasher.update(resource.content)
        resource.hash = hasher.hexdigest()
        try:
            self.select("SELECT id FROM content WHERE hash=?", resource.hash)
            raise DuplicateResource()
        except NoRow:
            pass

    def last_time(self, netloc):
        """ Return the last time a request was made to the specified domain,
            and record that a request is being made now. Returns 0 if this is
            the first request.
        """
        domain_id, t = self.select("SELECT id, time FROM domain " \
                                   "WHERE netloc=?", netloc)
        self.execute("UPDATE domain SET time=? WHERE id=?",
                     int(time()), domain_id)
        return t

    def parse_robots(self, netloc, content):
        """ Parse the given robots.txt content and store against the given
            domain. If content is None, any URL will be allowed.
        """
        robot = RobotFileParser()
        if content is not None:
            robot.parse(content.split("\n"))
        self.execute("UPDATE domain SET robots=? WHERE netloc=?",
                     dumps(robot), netloc)
        
    def check_robots(self, url):
        """ If no attempt has yet been made to fetch robots.txt for the domain
            of the specified URL, raise NoRobots. Otherwise, if access to the
            specified URL is not allowed according to the stored robots.txt,
            raise URLNotAllowed. Otherwise, return the crawl delay required by
            robots.txt, or None if not specified.
        """
        robots = self.select("SELECT robots FROM domain WHERE netloc=?",
                             url.netloc)
        if robots is None:
            raise NoRobots()
        robot = loads(str(robots))
        if not robot.can_fetch(crawler.user_agent, url.path):
            raise URLNotAllowed()
        return crawler.default_delay

    def stats(self):
        """ Output database stats to stdout.
        """
        n = self.select("SELECT COUNT(*) FROM content")
        print n, "URLs downloaded"
        n_e = self.select("SELECT COUNT(*) FROM error WHERE type='HTTPError'")
        print n_e, "HTTP errors:"
        for source, target, e in self.select_iter("SELECT src.url, tgt.url, " \
            "error FROM error, url tgt, link, url src WHERE type='HTTPError' "\
            "AND tgt.id=error.url_id AND tgt.id=target_id " \
            "AND src.id=source_id"):
            print "{0} => {1} ({2})".format(source, target, e)
        

if __name__ == "__main__":
    from sys import argv
    
    class SingleURLFollower:
        """ Trivial follow decider that only allows the initial URL.
        """
        def __init__(self, url):
            self.url = StdURL(url)
        
        def follow_url(self, resource, target):
            """ Follows no target URLs from links.
            """
            assert resource is not None
            assert target is not None
            raise URLNotFollowed()
        
        def follow_resource(self, resource):
            """ Allow only the initial URL to be followed.
            """
            if resource.origin_url != self.url:
                raise URLNotFollowed()
    
    if "-v" in argv[1:]:
        crawler.silent = False
    if "-q" in argv[1:]:
        crawler.default_delay = 0
    if "-t" in argv[1:]:
        crawler.http_threads = 1
    initialise = "-i" in argv[1:]
    domain = "-d" in argv[1:]
    single_url = "-u" in argv[1:]
    limit = 5 if "-l" in argv[1:] else None
    stats = "-s" in argv[1:]
    
    for arg in argv[1:]:
        if arg[0] == "-":
            argv.remove(arg)

    if len(argv) < (3 if not stats else 2):
        print """Usage: [-v|-q|-i|-s|-l] <db path> <initial URL>

Flags: -v  Output debug messages
       -q  Set default delay to 0
       -i  Initialise database (erases any data)
       -d  Do not follow links out of initial domain
       -u  Do not follow any URLs (single URL mode)
       -l  Limit the number of URLs crawled to 5
       -t  Run only one crawler thread
       -s  Don't crawl, but output database stats
"""
        exit()

    if initialise and isfile(argv[1]):
        unlink(argv[1])

    sql = SQLImplementation(argv[1])

    if initialise:
        sql.initialise()
    if stats:
        sql.stats()
    else:
        crawler.dump = sql
        crawler.pool = sql
        crawler.dns = sql
        crawler.follow = DefaultFollowDecider("^text/html$|^image/.*", domain)\
                         if not single_url else SingleURLFollower(argv[2])
        crawler.duplicate = sql
        crawler.parsers = (DefaultHtmlParser(), )
        crawler.throttle = sql
        crawler.robots = sql
        crawler.error = sql
        sql.add_url(StdURL(argv[2]))
        crawler.start()

    sql.close()
    
