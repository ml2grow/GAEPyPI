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

from .storage import GCStorage
from .package import Package, PackageIndex
from .exceptions import GAEPyPIError

import os
import webapp2
from cloudstorage import NotFoundError
from _decorators import basic_auth
from google.appengine.api import app_identity


class BaseHandler(webapp2.RequestHandler):
    """
    Basic handler class for our GAE webapp2 application
    """

    def write_page(self, body):
        self.response.write('<html><body>{}</body></html>'.format(body))

    def write404(self):
        self.response.set_status(404)
        self.write_page('<h1>Not found</h1>')

    def get_storage(self):
        bucket_name = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
        return GCStorage(bucket_name)


# Handlers
class IndexHandler(BaseHandler):
    """
    Handles /
    """

    @basic_auth()
    def get(self):
        self.write_page('<a href="/packages">packages</a>')

    @basic_auth(required_roles=['write'])
    def post(self):
        name = self.request.get('name', default_value=None)
        version = self.request.get('version', default_value=None)
        action = self.request.get(':action', default_value=None)
        upload = self.request.POST.getall('content')[0]
        content = upload.file.read()
        filename = upload.filename

        if name and version and content and action == 'file_upload':
            try:
                package = Package(self.get_storage(), name, version)
                package.put_file(filename, content)
            except GAEPyPIError as e:
                self.response.set_status(403)
                self.write_page('<h1>{0}</h1>'.format(str(e)))


class PypiHandler(BaseHandler):
    """
    Handles /pypi/
    """

    @basic_auth()
    def get(self):
        self.write_page(self.get_storage().to_html(full_index=True))


class PypiPackageHandler(BaseHandler):
    """
    Handles /pypi/package
    """

    @basic_auth()
    def get(self, package):
        storage = self.get_storage()
        index = PackageIndex(storage, package)
        if index.empty() or not index.exists(storage):
            self.write404()
            return
        self.write_page(index.to_html(full_index=True))


class PackageVersionHandler(BaseHandler):
    """
    Handles
       - /pypi/package/version
       - /packages/package/version
    """

    @basic_auth()
    def get(self, package, version):
        package = Package(self.get_storage(), package, version)
        if not package.exists():
            self.write404()
            return
        self.write_page(package.to_html())


class PackageBase(BaseHandler):
    """
    Handles /packages
    """

    @basic_auth()
    def get(self):
        storage = self.get_storage()
        if storage.empty():
            body = 'Nothing to see here yet, try uploading a package!'
        else:
            body = storage.to_html(full_index=False)
        self.write_page(body)


class PackageList(BaseHandler):
    """
    Handles /packages/package
    """

    @basic_auth()
    def get(self, package):
        index = PackageIndex(self.get_storage(), package)
        if not index.exists():
            self.write404()
        self.write_page(index.to_html(full_index=False))


class PackageDownload(BaseHandler):
    """
    Handles /packages/package/version/filename
    """

    @basic_auth()
    def get(self, name, version, filename):
        try:
            package = Package(self.get_storage(), name, version)
            with package.get_file(filename) as gcs_file:
                self.response.content_type = 'application/octet-stream'
                self.response.headers.add('Content-Disposition', 'attachment; filename={0}'.format(filename))
                self.response.write(gcs_file.read())
        except NotFoundError:
            self.write404()


__all__ = [cls.__name__ for cls in BaseHandler.__subclasses__()]
