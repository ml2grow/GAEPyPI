import mock
from gaepypi import Package, GAEPyPIError
import unittest


class TestPackage(unittest.TestCase):

    def _storage_mock(self, name, version, files):
        storage = mock.Mock()
        path = '/mybucket/packages/{0}/{1}'.format(name, version)
        storage.get_package_path = mock.Mock(return_value=path)
        if len(files) == 1:
            storage.split_path = mock.Mock(return_value={'filename': files[0]})
        storage.ls = mock.Mock(return_value=map(lambda f: path+'/'+f, files))
        return storage

    def test_instantiation(self):
        storage = self._storage_mock('dummy', '0.0.1', ['file.txt'])
        p = Package(storage, 'dummy', '0.0.1')

        storage.ls.assert_called_with('/mybucket/packages/dummy/0.0.1/')
        storage.get_package_path.assert_called_with('dummy', '0.0.1')
        assert p.name == 'dummy'
        assert p.version == '0.0.1'
        assert 'file.txt' in p.files
        assert len(p.files) == 1

    def test_no_capitals(self):
        storage = self._storage_mock('dummy', '0.0.1', [])
        p = Package(storage, 'Dummy', '0.0.1')

        storage.get_package_path.assert_called_with('dummy', '0.0.1')
        assert p.name == 'dummy'

    def test_name(self):
        storage = self._storage_mock('dummy', '0.0.1', [])
        p = Package(storage, 'dummy', '0.0.1')

        assert str(p) == 'dummy-0.0.1'

    def test_comparison(self):
        s1 = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        p1 = Package(s1, 'dummy', '0.0.1')
        s2 = self._storage_mock('dummy', '0.0.2', ['b.txt'])
        p2 = Package(s2, 'dummy', '0.0.2')

        assert p1 < p2
        assert not p2 < p1

    def test_comparison_name(self):
        s1 = self._storage_mock('b', '0.0.1', ['a.txt'])
        p1 = Package(s1, 'b', '0.0.1')
        s2 = self._storage_mock('a', '0.0.2', ['b.txt'])
        p2 = Package(s2, 'a', '0.0.2')

        assert p2 < p1

    def test_equality(self):
        s1 = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        p1 = Package(s1, 'dummy', '0.0.1')
        s2 = self._storage_mock('dummy', '0.0.1', ['b.txt'])
        p2 = Package(s2, 'dummy', '0.0.1')

        assert p1 == p2

    def test_equality_no_package(self):
        s1 = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        p1 = Package(s1, 'dummy', '0.0.1')

        assert not p1 == 'a'

    def test_exists(self):
        storage = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        storage.path_exists = mock.Mock(return_value=True)
        p = Package(storage, 'dummy', '0.0.1')

        assert p.exists()
        storage.path_exists.assert_called_with('/mybucket/packages/dummy/0.0.1')

    def test_not_exists(self):
        storage = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        storage.path_exists = mock.Mock(return_value=False)
        p = Package(storage, 'dummy', '0.0.1')

        assert not p.exists()
        storage.path_exists.assert_called_with('/mybucket/packages/dummy/0.0.1')

    def test_empty(self):
        storage = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        p1 = Package(storage, 'dummy', '0.0.1')
        assert not p1.empty()

        storage = self._storage_mock('dummy', '0.0.1', [])
        p2 = Package(storage, 'dummy', '0.0.1')
        assert p2.empty()

    def test_getfile_not_found(self):
        storage = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        p = Package(storage, 'dummy', '0.0.1')
        with self.assertRaises(GAEPyPIError):
            with p.get_file('b.txt') as f:
                pass

    def test_getfile(self):
        storage = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        p = Package(storage, 'dummy', '0.0.1')
        # Now some reconfiguration of storage mock
        fobj = mock.Mock()
        fobj.close = mock.Mock()
        storage.get_package_path = mock.Mock(return_value='/mybucket/packages/dummy/0.0.1/a.txt')
        storage.read = mock.Mock(return_value=fobj)

        with p.get_file('a.txt') as f:
            pass

        fobj.close.assert_called()
        storage.read.assert_called_with('/mybucket/packages/dummy/0.0.1/a.txt')
        storage.get_package_path.assert_called_with('dummy', '0.0.1', 'a.txt')

    def test_putfile_exists(self):
        storage = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        p = Package(storage, 'dummy', '0.0.1')
        with self.assertRaises(GAEPyPIError):
            with p.put_file('a.txt', 'content') as f:
                pass

    def test_putfile(self):
        storage = self._storage_mock('dummy', '0.0.1', ['a.txt'])
        p = Package(storage, 'dummy', '0.0.1')
        storage.write = mock.Mock()
        storage.get_package_path = mock.Mock(return_value='/mybucket/packages/dummy/0.0.1/b.txt')
        p.put_file('b.txt', 'content')

        assert 'b.txt' in p.files
        storage.get_package_path.assert_called_with('dummy', '0.0.1', 'b.txt')
        storage.write.assert_called_with('/mybucket/packages/dummy/0.0.1/b.txt', 'content')