#!/usr/bin/env python
#
# GAEPyPi, private package index on Google App Engine
# Copyright (C) 2017  ML2Grow BVBA

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import webapp2
from _handlers import *

app = webapp2.WSGIApplication([
    ('/', IndexHandler),
    ('/pypi/', PypiHandler),
    ('/pypi/([^/]+)/', PypiPackageHandler),
    ('/pypi/([^/]+)/([^/]+)', PackageVersionHandler),
    ('/packages', PackageBase),
    ('/packages/([^/]+)', PackageList),
    ('/packages/([^/]+)/([^/]+)', PackageVersionHandler),
    ('/packages/([^/]+)/([^/]+)/(.+)', PackageDownload)
], debug=True)