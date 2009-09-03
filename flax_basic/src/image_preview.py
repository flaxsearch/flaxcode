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

import os
import sys


def get_previewer():
    WINDOWS = (sys.platform == "win32")
    previewer = None

    if WINDOWS:
        try:
            import com_oo_preview
            previewer = com_oo_preview.get_previewer()
        except ImportError:
            previewer = None

        if not previewer:
            try:
                import uno_oo_preview
                previewer = uno_oo_preview.get_previewer()
            except ImportError:
                previewer = None

    preview_maker_map = {}
    if previewer:
        preview_maker_map.update( {'doc' : previewer.get_preview } )

    def make_preview(filename):
        unused, ext = os.path.splitext(filename)
        ext = ext[1:]
        try:
            return preview_maker_map[ext](filename)
        except KeyError:
            return None
    
    return make_preview
