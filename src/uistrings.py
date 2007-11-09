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
"""User interface strings.

This file is intended to be used as a single location for placing any strings
which are displayed in the user interface.  This allows translated versions of
the user interface to be generated more easily, since we only have to look in
this location (and, of course, in the html files in templates/) for text which
needs translating.

"""
__docformat__ = "restructuredtext en"

def log_level(level):
    """Get a description of a logger severity level.

    """
    return {
        'NOTSET': 'Default',
        'DEBUG': 'Debug',
        'INFO': 'Info',
        'WARNING': 'Warning',
        'ERROR': 'Error',
        'CRITICAL': 'Critical',
    }[level]

def msg(name):
    """Get a message for display.

    If the name of the message is not known, this raises an exception.

    """
    return {
        "auto_spell_corrected_msg": "The original query returned no results, the spell corrected query <em>%s</em> was used instead.",
        "spell_suggestion_msg": "Did you mean <a href=\"%(uri)s\">%(corrected)s</a>?",
    }[name]
