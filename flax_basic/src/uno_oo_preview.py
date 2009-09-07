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

import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.connection import NoConnectException

import ooutils

# This depends on an openoffice being available to convert things on
# localhost:8100 start with e.g.:

# openoffice.org -accept="socket,host=localhost,port=8100;urp;" -invisible -headless

# On windows. e.g.
# "C:\Program Files\OpenOffice.org 3\program\soffice.exe" -accept="socket,host=localhost,port=8100;urp;" -invisible -headless

class OOUnoPreviewer(ooutils.OOoImagePreviewer):

    def __init__(self):
        super(OOUnoPreviewer, self).__init__()
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local)
        context = resolver.resolve(
            "uno:socket,host=localhost,port=8100;urp;StarOffice.ComponentContext")
        self.desktop = context.ServiceManager.createInstanceWithContext(
            'com.sun.star.frame.Desktop', context)

    def make_prop(self, name, value):
        prop = PropertyValue()
        prop.Name = name
        if isinstance(value, (list, tuple)):
            prop.Value = uno.Any("[]com.sun.star.beans.PropertyValue", value)
        else:
            prop.Value = value
        return prop

def get_previewer():
    try:
        return OOUnoPreviewer()
    except NoConnectException:
        return None
