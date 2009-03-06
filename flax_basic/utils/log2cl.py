#!/usr/bin/env python
#
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
"""Simple script to update a ChangeLog from revision control entries.

Any existing ChangeLog is preserved; only entries which are newer than those in
the existing ChangeLog are created.

"""
__docformat__ = "restructuredtext en"

import os
from xml.sax.handler import ContentHandler
from xml.sax import parseString
import sys
import textwrap
import re
from datetime import datetime, timedelta
from time import strptime
import copy

blank_line = re.compile('\n\s*\n')

def collapse_groups(items, maxgroups):
    """Collapse a list of lists until there are only maxgroups items.

    """
    items = set((tuple(item) for item in items))
    while len(items) > maxgroups:
        # Find the best candidate to collapse
        groups = {}
        for item in items:
            for i in xrange(1, len(item)):
                key = tuple(item[:i])
                groups[key] = groups.get(key, 0) + 1

        # Any groups with a count of 1 should be disregarded, since
        # collapsing them doesn't help.
        for key, val in groups.iteritems():
            if val == 1:
                groups[key] = 0

        # Set parent counts to 0
        for key, val in groups.iteritems():
            if len(key) > 1 and val > 0:
                groups[key[:-1]] = 0
        groups = sorted([(val, key) for key, val in groups.iteritems()
                        if val != 0])
        if len(groups) == 0:
            break
        group = groups[-1][1]
        newitems = set()
        newitems.add(tuple([item for item in group] + ['']))
        for item in items:
            if item[:len(group)] != group:
                newitems.add(item)
        items = newitems

    return sorted(items)

class LogTextWrapper(textwrap.TextWrapper):

    def __init__(self, *args, **kwargs):
        textwrap.TextWrapper.__init__(self, *args, **kwargs)
        self.width = 68
        self.subsequent_indent = u'\t  '
        self.break_long_words = False

    def _split(self, text):
        chunks = textwrap.TextWrapper._split(self, text)
        newchunks = []
        for chunk in chunks:
            subchunks = chunk.split(',')
            for i in xrange(len(subchunks) - 1):
                if subchunks[i]:
                    subchunks[i] += ','
            newchunks.extend(subchunks)
        chunks = filter(None, newchunks)
        return chunks


class LogEntry(object):
    def __init__(self):
        self.date = None
        self.author = ''
        self.pathgroups = []

    def new_path_group(self):
        self.pathgroups.append([[], '', None])

    def add_path(self, path):
        self.pathgroups[-1][0].append(path)

    def add_msg(self, msg, addspace=False):
        if addspace:
            currmsg = self.pathgroups[-1][1]
            if len(msg) > 0 and not msg[0].isspace() and \
               len(currmsg) > 0 and not currmsg[-1].isspace():
                self.pathgroups[-1][1] += ' '
        self.pathgroups[-1][1] += msg

    def add_raw_msg(self, msg):
        if len(self.pathgroups) == 0:
            self.new_path_group()
        if self.pathgroups[-1][2] is None:
            self.pathgroups[-1][2] = msg
        else:
            self.pathgroups[-1][2] += msg

    def finalise(self):
        while len(self.pathgroups) > 0 and self.pathgroups[-1] == [[], '', None]:
            self.pathgroups = self.pathgroups[:-1]

    def __str__(self):
        result = []
        result.append(self.date.strftime('%a %b %d %H:%M:%S %%s %Y') %
                      self.tzname)
        result.append(u'  ')
        result.append(self.author)
        result.append(u'\n\n')
        for paths, msg, raw_msg in self.pathgroups:
            if raw_msg is not None:
                result.append(u'\t* ')
                result.append(raw_msg.strip().replace('\n', '\n\t').
                              replace('\n\t\n', '\n\n'))
                result.append(u'\n')
                continue

            paths = [path.split('/') for path in sorted(paths)]
            paths = collapse_groups(paths, 10)
            paths = ['/'.join(path) for path in paths]
            msg = u','.join(paths) + ': ' + msg.strip()
            # Wrap msg to 75 characters, but the first character is a tab,
            # so need to supply 75-7 as the width.
            paras = blank_line.split(msg)
            for i in xrange(len(paras)):
                initial_indent = u'\t* '
                if i > 0:
                    initial_indent = u'\t  '
                wrapper = LogTextWrapper(initial_indent=initial_indent)
                paras[i] = wrapper.fill(paras[i])

            result.append(u'\n\n'.join(paras))
            result.append(u'\n')

        return ''.join(result)

class LogEntries(object):
    def __init__(self):
        self.entries = []

    def append(self, entry, keepcl=False):
        entry.finalise()
        if len(entry.pathgroups) < 1:
            return
        if not keepcl and len(entry.pathgroups) == 1 and \
           entry.pathgroups[0][0] == ['ChangeLog']:
            return
        self.entries.append(entry)

    def __str__(self):
        return u'\n'.join([str(entry) for entry in self.entries])

    def extend(self, oldlog, use_old=False):
        if len(self.entries) == 0:
            self.entries.extend(oldlog.entries)
        if len(self.entries) == 0:
            return
        i = 0
        if use_old:
            # If an entry is in both the old and the new logs, use the old one
            while len(self.entries) > 0 and len(oldlog.entries) > 0 and \
                  self.entries[-1].date <= oldlog.entries[0].date:
                del self.entries[-1]
        else:
            # If an entry is in both the old and the new logs, use the new one
            while i < len(oldlog.entries) and \
                  self.entries[-1].date <= oldlog.entries[i].date:
                i += 1
        if i < len(oldlog.entries):
           self.entries.extend(oldlog.entries[i:])

class LogGetter(object):
    """A class which gets log entries from the revision control system.

    """
    def __init__(self, authors):
        self.authors = authors

    def get_log(self, toppath, path_prefix, olddate=None):
        raise NotImplementedError

class SvnInfoXmlHandler(ContentHandler):
    """XML parser for SVN info.

    """
    def __init__(self, authors):
        self.url = ''
        self.root = ''
        self.lastdate = ''
        self.lastauthor = ''

    def startElement(self, name, attrs):
        self.text = ''

    def endElement(self, name):
        if name == 'url':
            self.url = self.text
        elif name == 'root':
            self.root = self.text
        elif name == 'date':
            self.lastdate = self.text
        elif name == 'author':
            self.lastauthor = self.text
        self.text = ''

    def characters(self, text):
        self.text += text

class SvnXmlHandler(ContentHandler):
    """XML parser for SVN logs.

    """
    def __init__(self, authors, relpath, path_prefix):
        self.log = LogEntries()
        self.text = ''
        self.authors = authors
        self.relpath = relpath
        self.path_prefix = path_prefix
        self.msg_lines = ''
        self.paths = {}

    def startElement(self, name, attrs):
        if name == 'logentry':
            self.current = LogEntry()
            self.current.new_path_group()
            self.msg_lines = ''
            self.paths = {}
        else:
            self.text = ''

    def endElement(self, name):
        if name == 'logentry':
            inpathlist = 'maybe'
            msg = ''
            msg_lines = self.msg_lines.strip().split('\n')
            for linenum in range(len(msg_lines)):
                line = msg_lines[linenum].lstrip()
                # If a line starts with '* ' it's definitely a list of paths
                if line[:2] == '* ':
                    if inpathlist in ('no', 'maybe'):
                        inpathlist = 'yes'
                        self.current.add_msg(msg, addspace=True)
                        msg = ''
                    inpathlist = 'yes'
                    line = line[2:]

                if ':' in line:
                    # Try the whole message so far as a list of paths
                    msg2 = msg
                    if msg2 != '': msg2 += ' '
                    msg2 += line
                    paths, remnant = msg2.split(':', 1)
                    paths = paths.replace(', ', ',')
                    found_paths = False
                    found_all_paths = True
                    paths_found = []
                    for path in paths.split(','):
                        if path in self.paths or inpathlist == 'yes':
                            paths_found.append(path)
                            found_paths = True
                        else:
                            found_all_paths = False
                    if (inpathlist == 'yes' and found_paths) or \
                        (inpathlist == 'maybe' and found_all_paths):
                        inpathlist = 'maybe'
                        for path in paths_found:
                            self.current.add_path(path)
                            if path in self.paths:
                                del self.paths[path]
                        self.current.add_msg(remnant.lstrip(),
                                             addspace=True)
                        msg = ''
                        continue
                    # Try just the start of the current line as a list of
                    # paths
                    paths, remnant = line.split(':', 1)
                    paths = paths.replace(', ', ',')
                    found_paths = False
                    found_all_paths = True
                    paths_found = []
                    for path in paths.split(','):
                        if path in self.paths or inpathlist == 'yes':
                            paths_found.append(path)
                            found_paths = True
                        else:
                            found_all_paths = False
                    if found_paths and found_all_paths:
                        inpathlist = 'maybe'
                        self.current.add_msg(msg, addspace=True)
                        self.current.new_path_group()
                        for path in paths_found:
                            self.current.add_path(path)
                            del self.paths[path]
                        self.current.add_msg(remnant.lstrip(), addspace=True)
                        msg = ''
                        continue

                if line.strip() == '':
                    self.current.add_msg(msg, addspace=True)
                    msg = ''
                    inpathlist = 'maybe'
                    continue
                if msg != '': msg += ' '
                msg += line

            self.current.add_msg(msg, addspace=True)
            for path in self.paths:
                self.current.add_path(path)

            self.log.append(self.current)
        elif name == 'date':
            # FIXME - this parsing loses timezone information
            timetuple = strptime(self.text[:19], "%Y-%m-%dT%H:%M:%S")
            self.current.date = datetime(*timetuple[0:6])
            self.current.tzname = 'UTC'
        elif name == 'author':
            self.current.author = self.authors.get(self.text, self.text)
        elif name == 'path':
            path = self.text
            if path.startswith(self.relpath):
                path = path[len(self.relpath):]
            while path.startswith('/'):
                path = path[1:]
            path = self.path_prefix + path
            if len(path) == 0:
                path = '.'
            self.paths[path] = None
        elif name == 'msg':
            self.msg_lines += self.text
        self.text = ''

    def characters(self, text):
        self.text += text

class SvnLogGetter(LogGetter):
    """A class which gets log entries from SVN.

    """
    def get_log(self, toppath, path_prefix, olddate=None):
        origdir = os.getcwdu()
        try:
            os.chdir(toppath)

            (infh, outfh) = os.popen2(['svn', '--xml', 'info'])
            xmldata = outfh.read()
            infh.close()
            outfh.close()
            info = SvnInfoXmlHandler(self.authors)
            parseString(xmldata, info)

            relpath = info.url
            if info.url.startswith(info.root):
                relpath = info.url[len(info.root):]

            if olddate is None:
                (infh, outfh) = os.popen2(['svn', '--verbose', '--xml', 'log'])
            else:
                olddate = copy.copy(olddate)
                olddate += timedelta(seconds=1)
                (infh, outfh) = os.popen2(['svn', '--verbose', '--xml', 'log',
                                          '-r', 'HEAD:{%s}' % olddate])
            xmldata = outfh.read()
            infh.close()
            outfh.close()
            logs = SvnXmlHandler(self.authors, relpath, path_prefix)
            parseString(xmldata, logs)

            return logs.log
        finally:
            os.chdir(origdir)

def parse_time_followed_by_author(input, format):
    try:
        strptime(input, format)
        raise ValueError('Missing author')
    except ValueError, e:
        if str(e).startswith('unconverted data remains: '):
            excess_len = len(str(e)) - len('unconverted data remains: ')
        else:
            raise
    timetuple = strptime(input[:-excess_len], format)
    date = datetime(*timetuple[0:6])
    tzname = input[:-excess_len][20:-7]

    author = input[-excess_len:].strip()
    return date, tzname, author


class ChangeLogGetter(LogGetter):
    """A class which gets log entries from a ChangeLog file.

    """
    def get_log(self, toppath, path_prefix, olddate=None):
        origdir = os.getcwdu()
        try:
            os.chdir(toppath)
            log = LogEntries()

            try:
                fd = open('ChangeLog')
            except IOError:
                return log
            entry = None
            in_paths = False
            for line in fd:
                if not line[0].isspace():
                    # New entry
                    if entry is not None:
                        log.append(entry, keepcl=True)
                    entry = LogEntry()
                    in_paths = False

                    try:
                        date, tzname, author = parse_time_followed_by_author(line, "%a %b %d %H:%M:%S %Z %Y ")
                    except ValueError:
                        try:
                            date, tzname, author = parse_time_followed_by_author(line, "%a %b %d %H:%M:%S %Y ")
                            tzname = 'UTC'
                        except ValueError:
                            date, tzname, author = parse_time_followed_by_author(line, "%Y-%m-%d %H:%M ")
                            tzname = 'UTC'

                    entry.date = date
                    entry.tzname = tzname
                    entry.author = self.authors.get(author, author)
                else:
                    rawline = line.rstrip()
                    if rawline.startswith('\t'):
                        rawline = rawline[1:]
                    # Remove 4-space and 8-space indents
                    if rawline.startswith('    '):
                        rawline = rawline[4:]
                    if rawline.startswith('    '):
                        rawline = rawline[4:]
                    line = line.strip()
                    if line.startswith('* '):
                        line = line[2:]
                        rawline = rawline.strip()[2:]
                        entry.new_path_group()
                        paths = ''
                        in_paths = True

                    if in_paths:
                        if len(line) == 0:
                            entry.add_raw_msg('\n')
                        elif ':' in line:
                            entry.add_raw_msg(rawline + '\n')
                            rawline = None
                            linepaths, line = line.split(':', 1)
                            line.strip()
                            in_paths = False
                            paths = paths + linepaths
                            paths = paths.replace(', ', ',')
                            for path in paths.split(','):
                                entry.add_path(path)
                        else:
                            entry.add_raw_msg(rawline + '\n')
                            paths += line + ' '
                    if not in_paths:
                        if len(entry.pathgroups) == 0:
                            if len(line) != 0:
                                entry.new_path_group()
                                paths = ''
                                entry.add_msg(line + '\n')
                                if rawline is not None:
                                    entry.add_raw_msg(rawline + '\n')
                        else:
                            entry.add_msg(line + '\n')
                            if rawline is not None:
                                entry.add_raw_msg(rawline + '\n')

            if entry is not None:
                log.append(entry, keepcl=True)
            return log
        finally:
            os.chdir(origdir)

def guess_getter(authors):
    """Guess which revision control system we're in.

    Returns an appropriate getter.

    """
    # FIXME - implement - currently always says 'svn'
    return SvnLogGetter(authors)



if __name__ == '__main__':

    # FIXME - the following values should be held in a config file, or supplied
    # by command line parameters.
    authors = {
        'paul.x.rudin': 'Paul Rudin <paul@rudin.co.uk>',
        'boulton.rj': 'Richard Boulton <richard@lemurconsulting.com>',
        'banoffi': 'Tom Mortimer <tom@lemurconsulting.com>',
        'banoffi@gmail.com': 'Tom Mortimer <tom@lemurconsulting.com>',
        'rbolton': 'Richard Boulton <richard@lemurconsulting.com>',
        'alex.bowley': 'Alex Bowley',
        'charliejuggler': 'Charlie Hull <charlie@lemurconsulting.com>',
    }
    path_prefix = ''

    path = os.getcwdu()

    # Read the existing ChangeLog
    oldlog = ChangeLogGetter(authors).get_log(path, path_prefix)
    if len(oldlog.entries) > 0:
        olddate = oldlog.entries[0].date
    else:
        olddate = None

    # Get updates to the ChangeLog
    getter = guess_getter(authors)
    newlog = getter.get_log(path, path_prefix, olddate=olddate)

    # Combine the old and new
    newlog.extend(oldlog, True)

    # Write to the ChangeLog file
    try: os.unlink('ChangeLog.tmp')
    except OSError: pass
    fd = open('ChangeLog.tmp', 'w')
    fd.write(str(newlog))
    fd.close()
    try: os.unlink('ChangeLog')
    except OSError: pass
    os.rename('ChangeLog.tmp', 'ChangeLog')
