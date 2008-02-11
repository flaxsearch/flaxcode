# Copyright (C) 2007 Lemur Consulting Ltd
# Copyright (c) 2004-2007, CherryPy Team (team@cherrypy.org)

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


# Portions of this code are adapted from the cherrypy sources, to
# which the following applies:

# Copyright (c) 2004-2007, CherryPy Team (team@cherrypy.org)
# All rights reserved.

# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:

#     * Redistributions of source code must retain the above copyright notice,
#       this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright notice,
#       this list of conditions and the following disclaimer in the documentation
#       and/or other materials provided with the distribution.
#     * Neither the name of the CherryPy Team nor the names of its contributors
#       may be used to endorse or promote products derived from this software
#       without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""Replacement for the default cherrypy logmanager to better integrate
with Flax logging configuration."""

import logging
import datetime
import rfc822

import flaxlog
import cherrypy

class cpLogger(object):
    """A class to replace the cherrypy global log manager to
       facilitate integration with using the log configuration file to
       update logging configuration on the fly"""

    def __call__(self, msg='', context='', severity=logging.DEBUG, traceback=False):
        flaxlog.log(severity, 'webserver', ' '.join((context, msg)))

    # access string generation from cherrypy._cplogger.LogManager.access
    def access(self):
        request = cherrypy.request
        remote = request.remote
        response = cherrypy.response
        outheaders = response.headers
        tmpl = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
        s = tmpl % {'h': remote.name or remote.ip,
                    'l': '-',
                    'u': getattr(request, "login", None) or "-",
                    't': self.time(),
                    'r': request.request_line,
                    's': response.status.split(" ", 1)[0],
                    'b': outheaders.get('Content-Length', '') or "-",
                    'f': outheaders.get('referer', ''),
                    'a': outheaders.get('user-agent', ''),
                    }
        flaxlog.info('webserver', s)

    # from cherrypy._cplogger.LogManager
    def time(self):
        """Return now() in Apache Common Log Format (no timezone)."""
        now = datetime.datetime.now()
        month = rfc822._monthnames[now.month - 1].capitalize()
        return ('[%02d/%s/%04d:%02d:%02d:%02d]' %
                (now.day, month, now.year, now.hour, now.minute, now.second))

