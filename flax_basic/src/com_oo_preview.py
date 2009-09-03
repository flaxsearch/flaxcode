# Copyright (C) 2009 Lemur Consulting Ltd
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

from win32com.client.dynamic import Dispatch
import pywintypes
import pythoncom

import ooutils

class OOoComPreviewer(ooutils.OOoImagePreviewer):

    def __init__(self):
        self.service_man = Dispatch('com.sun.star.ServiceManager')
        self.service_man._FlagAsMethod("Bridge_GetStruct")
        self.desktop = self.service_man.CreateInstance(
            'com.sun.star.frame.Desktop') 

    def make_prop(self, name, value):
        prop = self.service_man.Bridge_GetStruct(
            'com.sun.star.beans.PropertyValue')
        prop.Name = name
        prop.Value = value
        return prop

def get_previewer():
    return OOoComPreviewer()
