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

r"""Flax actions are 

See flaxcode/applications/xml_indexer and simple_search for examples of how
to use Flax Core.

FIXME - add some tests!

"""

from __future__ import with_statement

import re
import time
import xapian
from errors import ActionsError

conf_re_1 = re.compile(r'\s+(\w+):(.*)')            # field def
conf_re_2 = re.compile(r'(\w+)\(([^\)]*)\)|(\w+)')  # actions

class _IndexerAction(object):
    """Base class for actions.
    
    """
    isfilter = None

    def __init__(self):
        self.next = None 
        
    def __call__(self, fieldname, value, doc):
        raise NotImplemented
        
    def add_action(self, action):
        self.next = action
        
    def __repr__(self):
        if self.next:
            return str(self) + '->' + repr(self.next)
        else:
            return str(self)


class DateAction(_IndexerAction):
    """FIXME
    """
    action_name = 'date'
    isfilter = True
    
    def __init__(self, format):
        _IndexerAction.__init__(self)
        self.format = format

    def __call__(self, fieldname, value, doc):        
        date = time.strptime(value, self.format)
        doc.index(fieldname, date)
        if self.next: self.next(fieldname, value, doc)
        
    def __str__(self):
        return 'DateAction(%s)' % self.format


class FilterAction(_IndexerAction):
    action_name = 'filter'
    isfilter = True

    def __init__(self, *args):
        _IndexerAction.__init__(self)
        self.facet = False
        self.isdocid = False
        
        for arg in args:
            if arg == 'facet':
                self.facet = True
            elif arg == 'docid':
                self.isdocid = True
            else:
                raise ActionsError, 'unknown filter argument: %s' % arg
    
    def __call__(self, fieldname, value, doc):
        doc.index(fieldname, value, store_facet=self.facet, isdocid=self.isdocid)
        if self.next: self.next(fieldname, value, doc)

    def __str__(self):
        return 'FilterAction'


class NumericAction(_IndexerAction):
    action_name = 'numeric'
    isfilter = True
    
    def __call__(self, fieldname, value, doc):
        try:
            doc.index(fieldname, int(value))
        except ValueError:
            doc.index(fieldname, float(value))
        if self.next: self.next(fieldname, value, doc)

    def __str__(self):
        return 'NumericAction'


class StripTagsAction(_IndexerAction):
    """Strip markup tags etc out of text.
    
    """
    action_name = 'striptags'
    re_tag = re.compile(r'</\w+>|<\w{1,20}[^>]{0,100}>')

    def __call__(self, fieldname, value, doc):
        value = self.re_tag.sub('', value)
        if self.next: self.next(fieldname, value, doc)

    def __str__(self):
        return 'StripTagsAction'

class ReSearchAction(_IndexerAction):
    """Do a regex search on the text and return the result as a string.

    """
    action_name = 'research'

    def __init__(self, *args, **kwargs):
        _IndexerAction.__init__(self)
        self.re = re.compile(args[0], re.I)

    def __call__(self, fieldname, value, doc):
        m = self.re.search(value)
        if m and self.next:
            self.next(fieldname, m.group(0), doc) 

    def __str__(self):
        return 'ReSearchAction'

class IndexAction(_IndexerAction):
    action_name = 'index'
    isfilter = False
    
    def __init__(self, *args, **kwargs):
        _IndexerAction.__init__(self)
        self.weight = 1
        self.spelling = False
        self.default = False
        
        for v in args:
            if v == 'spell':
                self.spelling = True
            elif v == 'default':
                self.default = True
            else:
                raise ActionsError, 'unknown index parameter: %s' % v
        
        for k, v in kwargs.iteritems():
            if k == 'weight':
                self.weight = int(v)
            else:
                raise ActionsError, 'unknown index parameter: %s=%s' % (k, v)

    def __call__(self, fieldname, value, doc):        
        doc.index(fieldname, value, 
                  search_default=self.default,
                  spelling=self.spelling, 
                  weight=self.weight)
        if self.next: self.next(fieldname, value, doc)

    def __str__(self):
        return 'IndexAction[w=%s s=%s d=%s]' % (self.weight, self.spelling, self.default)


class SplitAction(_IndexerAction):
    action_name = 'split'
    
    def __init__(self, pattern):
        _IndexerAction.__init__(self)
        self.re = re.compile(pattern)
        
    def __call__(self, fieldname, value, doc):
        if self.next:
            for v in self.re.split(value):
                self.next(fieldname, v, doc)

    def __str__(self):
        return 'SplitAction(%s)' % self.re


class SliceAction(_IndexerAction):
    action_name = 'slice'
    
    def __init__(self, begin, end):
        _IndexerAction.__init__(self)
        self.begin = int(begin)
        self.end = int(end)

    def __call__(self, fieldname, value, doc):        
        if self.next: self.next(fieldname, value[self.begin:self.end], doc)

    def __str__(self):
        return 'SliceAction(%s, %s)' % (self.begin, self.end)


# create a map of command names to classes
_map = {}
for x in globals().values():
    try:
        assert x.action_name not in _map
        _map[x.action_name] = x
    except AttributeError:
        pass

class FieldAction(object):
    """Object representing an action on a fieldname at an xpath.
    
    FIXME: explain this better!
    """
    def __init__(self, fieldname, extkey, action):
        self.fieldname = fieldname
        self.external_key = extkey
        self.action = action
        
def parse_actions(conffile):
    """Parse the config file and return a list of FieldAction objects.
    
    FIXME: document file syntax and actions chains!
    """

    actions = []
    extkey = None
    with open(conffile) as f:        
        for lineno, line in enumerate(f):
            if line.isspace() or line[0] == '#': 
                continue
            
            if not line[0].isspace():
                # new external key
                extkey = line.strip()
            else:
                # field def
                m1 = conf_re_1.match(line)
                if not m1:
                    raise ActionsError, 'syntax error in %s, line %d' % (
                        conffile, lineno)
                
                fieldname = m1.group(1)
                curact = None
                for m2 in conf_re_2.finditer(m1.group(2)):
                    grp = m2.groups()
                    args = []
                    kwargs = {}
                    if grp[0]:
                        actname = grp[0]
                        for actarg in grp[1].split():
                            bits = actarg.split('=')
                            if len(bits) == 1:
                                args.append(actarg)
                            elif len(bits) == 2:
                                kwargs[bits[0]] = bits[1]
                            else:
                                raise ActionsError, 'syntax error in %s, line %d' % (
                                    conffile, lineno)
                    elif grp[2]:
                        actname = grp[2]                    
                    else:
                        raise ActionsError, 'syntax error in %s, line %d' % (
                            conffile, lineno)
                    
                    action = _map[actname](*args, **kwargs)
                    if curact:
                        curact.add_action(action)
                    else:
                        if extkey is None:
                            raise ActionsError, 'syntax error in %s, line %d' % (
                                conffile, lineno)
                        actions.append(FieldAction(fieldname, extkey, action))
                    curact = action

        # FIXME validate actions, e.g. no filter & index in same chain/field, facets etc
                    
        return actions

if __name__ == '__main__':
    import sys
    for field in parse_actions(sys.argv[1]):
        print field.external_key
        print '    %s: %r' % (field.fieldname, field.action)

