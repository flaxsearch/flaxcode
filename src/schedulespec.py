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
"""A specification for performing periodic indexing.

"""
__docformat__ = "restructuredtext en"

import itertools

class ScheduleSpec(object):
    """The options for scheduling indexing of a document collection.

    """
    _wildcard = '*'
    _empty = ""

    def __init__(self, **kwargs):
        self.update(**kwargs)

    def parse_string_spec(self, spec):
        if not isinstance(spec, str):
            return spec
        stripped = spec.strip()
        if (stripped == self._wildcard) or (stripped == self._empty):
            return stripped
        return [int(x) for x in stripped.split(',')]

    def update(self,
               mins = _empty,
               hours = _empty,
               monthdays = _empty,
               weekdays = _empty,
               months = _empty,
               **kwargs):

        self.mins = self.parse_string_spec(mins)
        self.hours = self.parse_string_spec(hours)
        self.monthdays = self.parse_string_spec(monthdays)
        self.weekdays = self.parse_string_spec(weekdays)
        self.months = self.parse_string_spec(months)

    def wildcarded(self, prop):
        return prop == self._wildcard

    def _matches(self, candidate, prop):
        return not (prop == self._empty) and (self.wildcarded(prop) or (candidate in prop))

    def matching_time(self, date_time):
        """Determine whether the datetime.datetime object provided matches the
        filespec.

        """
        return all(itertools.starmap(self._matches,
                                     ((date_time.month, self.months),
                                      (date_time.day, self.monthdays),
                                      (date_time.weekday(), self.weekdays),
                                      (date_time.hour, self.hours),
                                      (date_time.minute, self.mins))))
