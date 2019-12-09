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

from .package import PackageIndex
from .templates import __templates__
from .renderable import Renderable

import six
from abc import ABCMeta, abstractmethod
import cloudstorage as gcs

my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)


@six.add_metaclass(ABCMeta)
class Storage(Renderable):
    """
    Storage abstract class, describing the interface assumed by the Package/PackageIndex classes
    """

    @abstractmethod
    def get_packages_path(self):
        """
        :return: (string) path to all package folders
        """
        pass

    @abstractmethod
    def get_package_path(self, package, version=None, filename=None):
        """
        Produce the package path
        :param package: package name
        :param version: package version
        :param filename: specific file
        """
        pass

    @abstractmethod
    def split_path(self, path):
        """
        Break down a path into package/version/file (if present)
        :param path: string
        :return: dictionary with keys package, version and filename
        """
        pass

    @abstractmethod
    def ls(self, path, dir_only=False):
        """
        list all nodes below a given path.
        :param path: scan this path
        :param dir_only: only include directories
        :return: iterable
        """
        pass

    @abstractmethod
    def read(self, path):
        """
        Read a specific file
        :param path: path to file
        :return: file object
        """
        pass

    @abstractmethod
    def write(self, path, content):
        """
        Write content to file
        """
        pass

    @abstractmethod
    def file_exists(self, path):
        """
        Query if a file exists
        """
        pass

    def empty(self):
        """
        Verify if any packages are present in the storage
        """
        return len(PackageIndex.get_all(self)) == 0

    def to_html(self, full_index=True):
        """
        Render overview of all packages in storage
        :param full_index: if true, print all files for all versions. if false, only print package names (once)
        """
        package_indices = PackageIndex.get_all(self)
        template_file = 'storage-index.html.j2' if not full_index else 'package-index.html.j2'
        template = __templates__.get_template(template_file)
        return template.render({'indices': package_indices})


class GCStorage(Storage):
    """
    Implementation of the Storage abstract class for Google Cloud Storage
    """
    def __init__(self, bucket, acl='project-private'):
        self.bucket = bucket
        self.acl = acl

    def get_packages_path(self):
        return '/{0}/packages'.format(self.bucket)

    def get_package_path(self, package, version=None, filename=None):
        path = '{0}/{1}'.format(self.get_packages_path(), package)
        if version:
            path = '{0}/{1}'.format(path, version)
            if filename:
                path = '{0}/{1}'.format(path, filename)
        return path

    def split_path(self, path):
        segments = path.split('/')
        assert segments[1] == self.bucket
        segments = segments[3:-1] if segments[-1] == '' else segments[3:]
        components = ['package', 'version', 'filename']
        return dict(zip(components, segments))

    def ls(self, path, dir_only=False):
        padded = path if path[-1] == '/' else path+'/'
        return [f.filename for f in gcs.listbucket(padded, delimiter='/') if f.is_dir or not dir_only]

    def read(self, path):
        return gcs.open(path)

    def write(self, path, content):
        write_retry_params = gcs.RetryParams(backoff_factor=1.1)
        gcs_file = gcs.open(path, 'w', options={'x-goog-acl': self.acl}, retry_params=write_retry_params)
        gcs_file.write(content)
        gcs_file.close()

    def file_exists(self, path):
        match = list(gcs.listbucket(path.rstrip('/')))
        return path.rstrip('/') in [stat.filename for stat in match]

    def path_exists(self, path):
        match = list(gcs.listbucket(path.rstrip('/'), delimiter='/'))
        return path.rstrip('/') in [stat.filename.rstrip('/') for stat in match]
