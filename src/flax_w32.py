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
"""Start flax as Windows Command Line Application, encapsulate Registry reads.

"""
__docformat__ = "restructuredtext en"


import win32api
import regutil
import os
import sys

REGKEY_BASE = "SOFTWARE\\Lemur Consulting Ltd\\Flax\\"
DEFAULT_INSTALL_DIR = r"c:\Program Files\Flax"

class FlaxRegistry(object):
    """Encapsulate all the settings we read from the Registry
    """

    # We need to do a lot of messing about with paths, as when running as a frozen executable
    # (under Windows using Py2exe)  it's not clear what our actual path is. 

    def __init__(self):

        self.runtimepath = None
        self.datapath = None

        try:
            self.runtimepath = win32api.RegQueryValue(regutil.GetRootKey(),
                                            REGKEY_BASE + "RuntimePath")
        except:
            self.runtimepath = DEFAULT_INSTALL_DIR
    
        try:
            self.datapath = win32api.RegQueryValue(regutil.GetRootKey(),
                                        REGKEY_BASE + "DataPath")
        except:
            self.datapath = DEFAULT_INSTALL_DIR

