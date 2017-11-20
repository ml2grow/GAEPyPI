from gaepypi import Package, PackageIndex, GAEPyPIError
import mock
import unittest


class ResponseList(object):
    def __init__(self, *args):
        super(ResponseList, self).__init__()
        self.responses = args
        self._counter = 0

    def __call__(self, *args, **kwargs):
        val = self.responses[self._counter % len(self.responses)]
        self._counter += 1
        return val


class TestPackageIndex(unittest.TestCase):

    def _storage_mock(self, name, version, files):
        storage = mock.Mock()
        path = '/mybucket/packages/{0}/{1}'.format(name, version)
        storage.get_package_path = mock.Mock(return_value=path)
        if len(files) == 1:
            storage.split_path = mock.Mock(return_value={'filename': files[0]})
        storage.ls = mock.Mock(return_value=map(lambda f: path+'/'+f, files))
        return storage

    def setUp(self):
        # Prepare storage interactions
        self.storage = mock.Mock()
        path = '/mybucket/packages/dummy'
        self.storage.get_package_path = mock.Mock(side_effect=ResponseList(path, path + '/0.0.1', path + '/0.0.2'))
        self.storage.ls = mock.Mock(
            side_effect=ResponseList(['/mybucket/packages/dummy/0.0.1', '/mybucket/packages/dummy/0.0.2'],
                                     ['/mybucket/packages/dummy/0.0.1/a.whl'],
                                     ['/mybucket/packages/dummy/0.0.2/b.whl']))
        self.storage.split_path = mock.Mock(side_effect=ResponseList(dict(version='0.0.1'),
                                                                dict(version='0.0.2'),
                                                                dict(filename='a.whl'),
                                                                dict(filename='b.whl')))

        self.index = PackageIndex(self.storage, 'dummy')

    def test_instantiation(self):
        # Verify calls
        self.storage.get_package_path.assert_has_calls([mock.call('dummy'),
                                                   mock.call('dummy', '0.0.1'),
                                                   mock.call('dummy', '0.0.2')])
        self.storage.ls.assert_has_calls([mock.call('/mybucket/packages/dummy', dir_only=True),
                                     mock.call('/mybucket/packages/dummy/0.0.1/'),
                                     mock.call('/mybucket/packages/dummy/0.0.2/')])
        self.storage.split_path.assert_has_calls([mock.call('/mybucket/packages/dummy/0.0.1'),
                                             mock.call('/mybucket/packages/dummy/0.0.2'),
                                             mock.call('/mybucket/packages/dummy/0.0.1/a.whl'),
                                             mock.call('/mybucket/packages/dummy/0.0.2/b.whl')])
        assert self.index.name == 'dummy'
        assert self.index.size == len(self.index) == 2
        assert not self.index.empty()

    def test_content(self):
        s1 = self._storage_mock('dummy', '0.0.1', ['a.whl'])
        s2 = self._storage_mock('dummy', '0.0.2', ['b.whl'])
        s3 = self._storage_mock('dummy', '0.0.3', ['c.whl'])

        p1 = Package(s1, 'dummy', '0.0.1')
        p2 = Package(s2, 'dummy', '0.0.2')
        p3 = Package(s3, 'dummy', '0.0.3')

        assert p1 in self.index
        assert p2 in self.index
        assert p3 not in self.index

    def test_get_version(self):
        with self.assertRaises(GAEPyPIError):
            self.index.get_version('0.0.3')

        p = self.index.get_version('0.0.2')
        assert isinstance(p, Package)
        assert p.name == 'dummy'
        assert p.version == '0.0.2'
        assert p.files == set(['b.whl'])

    def test_add_version(self):
        s3 = self._storage_mock('dummy', '0.0.3', ['c.whl'])
        p3 = Package(s3, 'dummy', '0.0.3')
        self.index.add(p3)
        assert p3 in self.index
        assert self.index.size == 3

    def test_add_version_incorrect_name(self):
        s3 = self._storage_mock('wheel', '0.0.3', ['c.whl'])
        p3 = Package(s3, 'wheel', '0.0.3')
        with self.assertRaises(GAEPyPIError):
            self.index.add(p3)

    def test_add_version_exists(self):
        s2 = self._storage_mock('dummy', '0.0.2', ['b.whl'])
        p2 = Package(s2, 'dummy', '0.0.2')
        with self.assertRaises(GAEPyPIError):
            self.index.add(p2)

    def test_exists(self):
        self.storage.get_package_path = mock.Mock(return_value='/mybucket/packages/dummy')
        self.storage.path_exists = mock.Mock(return_value=True)
        assert self.index.exists()
        self.storage.path_exists.assert_called_with('/mybucket/packages/dummy')

    def test_not_exists(self):
        self.storage.get_package_path = mock.Mock(return_value='/mybucket/packages/dummy')
        self.storage.path_exists = mock.Mock(return_value=False)
        assert not self.index.exists()
        self.storage.path_exists.assert_called_with('/mybucket/packages/dummy')

