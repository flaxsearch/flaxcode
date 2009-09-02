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


import sys
import os
import zipfile
import subprocess
import tempfile

WINDOWS = (sys.platform == "win32")

# We can interface with OO in two ways - either via a socket to a
# running OO instance - this depends on an openoffice being available to
# convert things on localhost:8100 start with e.g.: 

#openoffice.org -accept="socket,host=localhost,port=8100;urp;"
#-invisible -headless

# On windows we can use com - this is probably preferable since it
# doesn't depend on binary compatibility of the python modules. Here
# we're use late binding - early binding would probably be better
# performance wise.

# FIXME: at the moment binding the ServiceManager and Desktop objects
# to globals results in dispatching problems when using com. I think
# this is probably something to do with the threading, but I'm not
# sure. There must be an overhead in repeatedly getting them as we do
# at the moment. Although I'm not sure whether it's significant. The
# best approach may be to have a single threaded process that serves
# requests to make images via some kind of interprocess call. 

# FIXME: the temporary files that we make hang about on windows - we
# get an error because the OOo process still has a handle on
# them. Ideally we should clean them up.

# TODO: is it necessary to actually make the odt file on disk?

try:
    from win32com.client.dynamic import Dispatch
    import pywintypes
    import pythoncom

    def get_sm():
        service_man = Dispatch('com.sun.star.ServiceManager')
        service_man._FlagAsMethod("Bridge_GetStruct")
        return service_man

    def make_prop(name, value):
        prop = get_sm().Bridge_GetStruct('com.sun.star.beans.PropertyValue')
        prop.Name = name
        prop.Value = value
        return prop
except (ImportError, pywintypes.com_error):
    # OO not installed or not probably registered with COM infrastructure
    get_sm, make_prop =  None, None

if not get_sm: #failed to get via com - we try uno import instead.
    try:
        import uno
        from com.sun.star.beans import PropertyValue
        from com.sun.star.connection import NoConnectException
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext(
            "com.sun.star.bridge.UnoUrlResolver", local)
        try:
            context = resolver.resolve(
                "uno:socket,host=localhost,port=8100;urp;StarOffice.ComponentContext")
        except NoConnectException:
            service_man, make_prop, coInit = None, None, lambda : None
        if context:

            def get_sm():
                return context.ServiceManager.createInstanceWithContext(
                    "com.sun.star.frame.Desktop", context)
            
            def make_prop(name, value):
                prop = PropertyValue()
                prop.Name = name
                prop.Value = value
                return prop

    except ImportError:
        get_sm, make_prop = None, None


def get_desktop():
    # binding deskop to a global sometimes fails - not sure why
    if get_sm:
        return get_sm().CreateInstance('com.sun.star.frame.Desktop') 
    else:
        return None

def make_props(prop_pairs):
    return [make_prop(*pair) for pair in prop_pairs]

def convert_file_to_oo(infile, outfile):
    desktop = get_desktop()

    if not desktop:
        return False

    document = desktop.loadComponentFromURL(
        filename_to_url(infile) ,"_blank", 0, make_props([("Hidden", True)]))

    if document:
        props = make_props((("FilterName", "writer8"),))
        document.storeToURL(filename_to_url(outfile), props)
        document.close(False)
        return True

def filename_to_url(filename):
    filename = os.path.normpath(filename)
    filename = filename.replace("\\", "/")
    return "file:///" + filename


def make_doc_preview_oo(filename, width, height):
    temp = tempfile.mktemp(suffix=".odt")
    if convert_file_to_oo(filename, temp):
        z = zipfile.ZipFile(temp)
        p = z.open('Thumbnails/thumbnail.png')
        rv = p.read()
#        if os.path.exists(temp):
#            os.remove(temp)
        return rv


preview_maker_map = {'doc' : make_doc_preview_oo }

def make_preview(filename, width=100, height=100):
    unused, ext = os.path.splitext(filename)
    ext = ext[1:]
    try:
        return preview_maker_map[ext](filename, width, height)
    except KeyError:
        return None
