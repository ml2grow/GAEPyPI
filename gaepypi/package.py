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

from .exceptions import GAEPyPIError
from .templates import __templates__
from .renderable import Renderable

import six
from contextlib import contextmanager
from abc import ABCMeta, abstractmethod


@six.add_metaclass(ABCMeta)
class BucketObject(Renderable):
    def __init__(self, storage, *args, **kwargs):
        super(BucketObject, self).__init__(*args, **kwargs)
        self.storage = storage

    def enquire_storage(self, storage):
        return storage or self.storage

    @abstractmethod
    def exists(self):
        pass


class Package(BucketObject):
    """
    Class representing a Python package (name, version and files)
    """

    def __init__(self, storage, name, version):
        super(Package, self).__init__(storage)
        self.name = name.lower()
        self.version = version

        files = []
        path = storage.get_package_path(name.lower(), version)
        for f in storage.ls(path+'/'):
            files.append(storage.split_path(f)['filename'])
        self.files = set(files)

    def __str__(self):
        return '{0}-{1}'.format(self.name, self.version)

    def __lt__(self, other):
        return self.version < other.version if self.name == other.name else self.name < other.name

    def __eq__(self, other):
        return isinstance(other, Package) \
               and self.name == other.name \
               and self.version == other.version

    def __hash__(self):
        return hash((self.name, self.version))

    def exists(self, storage=None):
        storage = self.enquire_storage(storage)
        version_path = storage.get_package_path(self.name, self.version)
        return storage.path_exists(version_path)

    def to_html(self):
        template = __templates__.get_template('package-index.html.j2')
        return template.render({'indices': [[self]]})

    def empty(self):
        return len(self.files) == 0

    @contextmanager
    def get_file(self, filename, storage=None):
        if filename not in self.files:
            raise GAEPyPIError("File not found for {0}".format(self))
        storage = self.enquire_storage(storage)
        path = storage.get_package_path(self.name, self.version, filename)
        gcs_file = storage.read(path)
        yield gcs_file
        gcs_file.close()

    def put_file(self, filename, content, storage=None):
        if filename in self.files:
            err_msg = "File {0} has already been added to {1}, upload a new version".format(filename, self)
            raise GAEPyPIError(err_msg)
        storage = self.enquire_storage(storage)
        path = storage.get_package_path(self.name, self.version, filename)
        storage.write(path, content)
        self.files.add(filename)


class PackageIndex(BucketObject, set):
    """
    Class representing a package index (for a name, all versions present in storage)
    """

    @classmethod
    def get_all(cls, storage):
        """
        Get all Package indices for a given storage
        :return: iterable of PackageIndex
        """
        path = storage.get_packages_path()
        packages = storage.ls(path, dir_only=True)
        return [cls(storage, storage.split_path(package_path)['package']) for package_path in packages]

    def __init__(self, storage, name):
        package_path = storage.get_package_path(name.lower())
        contents = storage.ls(package_path, dir_only=True)
        versions = [storage.split_path(version_path)['version'] for version_path in contents]
        super(PackageIndex, self).__init__(storage, [Package(storage, name, v) for v in versions])
        self.name = name

    def __str__(self):
        return "Package Index for {0}".format(self.name)

    def __lt__(self, other):
        return self.name < other.name

    @property
    def size(self):
        return len(self)

    def empty(self):
        return self.size == 0

    def exists(self, storage=None):
        storage = self.enquire_storage(storage)
        package_path = storage.get_package_path(self.name)
        return storage.path_exists(package_path)

    def add(self, other):
        """
        Add version to index
        :param other: instance of Package, with matching name and distinct version.
        """
        assert isinstance(other, Package)
        if self.name != other.name:
            raise GAEPyPIError("Package {0} can not be added to {1} (name differs)".format(other, self))

        if other in self:
            raise GAEPyPIError("Version already exists, you should upload a different version.")

        super(PackageIndex, self).add(other)

    def to_html(self, full_index=True):
        if full_index:
            template = __templates__.get_template('package-index.html.j2')
            return template.render({'indices': [self]})
        else:
            template = __templates__.get_template('version-index.html.j2')
            return template.render({'packages': self})

    def get_version(self, version):
        """
        Get package of specific version from the index
        :return: Package object of given version
        """
        for p in self:
            if p.version == version:
                return p
        raise GAEPyPIError("Version {0} not found!".format(version))
