from google.appengine.ext import testbed
from gaepypi import GCStorage
from mock import patch, Mock, PropertyMock
import unittest


class TestGCSStorage(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_app_identity_stub()
        self.testbed.init_datastore_v3_stub()
        self.s = GCStorage('mybucket')

    def tearDown(self):
        self.testbed.deactivate()

    def test_packages_path(self):
        assert self.s.get_packages_path() == '/mybucket/packages'

    def test_package_path(self):
        assert self.s.get_package_path('dummy') == '/mybucket/packages/dummy'
        assert self.s.get_package_path('dummy', '0.0.1') == '/mybucket/packages/dummy/0.0.1'
        assert self.s.get_package_path('dummy', '0.0.1', 'file.txt') == '/mybucket/packages/dummy/0.0.1/file.txt'


    def test_split_path(self):
        assert self.s.split_path('/mybucket/packages/dummy') == {'package': 'dummy'}
        assert self.s.split_path('/mybucket/packages/dummy/') == {'package': 'dummy'}
        assert self.s.split_path('/mybucket/packages/dummy/0.0.1') == {'package': 'dummy', 'version': '0.0.1'}
        assert self.s.split_path('/mybucket/packages/dummy/0.0.1/file.txt') == {'package': 'dummy',
                                                                                'version': '0.0.1',
                                                                                'filename': 'file.txt'}

    @patch('gaepypi.storage.gcs.listbucket')
    def test_file_exists(self, mock):
        m = Mock()
        type(m).is_dir = PropertyMock(return_value=False)
        type(m).filename = PropertyMock(return_value='/mybucket/file.txt')
        mock.return_value = [m]
        assert self.s.file_exists('/mybucket/file.txt')
        mock.assert_called_with('/mybucket/file.txt')

    @patch('gaepypi.storage.gcs.listbucket')
    def test_file_not_exists(self, mock):
        mock.return_value = []
        assert not self.s.file_exists('/mybucket/file.txt')
        mock.assert_called_with('/mybucket/file.txt')

    @patch('gaepypi.storage.gcs.listbucket')
    def test_file_is_dir(self, mock):
        m = Mock()
        type(m).is_dir = PropertyMock(return_value=True)
        mock.return_value = [m]
        assert not self.s.file_exists('/mybucket/file')
        mock.assert_called_with('/mybucket/file')

    @patch('gaepypi.storage.gcs.listbucket')
    def test_path_is_dir(self, mock):
        m = Mock()
        type(m).is_dir = PropertyMock(return_value=True)
        type(m).filename = PropertyMock(return_value='/mybucket/file')
        mock.return_value = [m]
        assert self.s.path_exists('/mybucket/file')
        mock.assert_called_with('/mybucket/file', delimiter='/')

    @patch('gaepypi.storage.gcs.listbucket')
    def test_path_exists(self, mock):
        m = Mock()
        type(m).is_dir = PropertyMock(return_value=False)
        type(m).filename = PropertyMock(return_value='/mybucket/file.txt')
        mock.return_value = [m]
        assert self.s.path_exists('/mybucket/file.txt')
        mock.assert_called_with('/mybucket/file.txt', delimiter='/')

    @patch('gaepypi.storage.gcs.listbucket')
    def test_ls_all(self, mock):
        files = []
        filenames = list(map(lambda f: '/mybucket/path/{0}'.format(f), ['dummy', 'a.txt', 'b.txt', 'wheel']))
        for isdir, filename in zip([True, False, False, True], filenames):
            m = Mock()
            type(m).is_dir = PropertyMock(return_value=isdir)
            type(m).filename = PropertyMock(return_value=filename)
            files.append(m)
        mock.return_value = files
        retrieved = self.s.ls('/mybucket/path/')
        mock.assert_called_with('/mybucket/path/', delimiter='/')
        assert len(retrieved) == 4
        assert filenames == retrieved

    @patch('gaepypi.storage.gcs.listbucket')
    def test_ls_dir_only(self, mock):
        files = []
        filenames = list(map(lambda f: '/mybucket/path/{0}'.format(f), ['dummy', 'a.txt', 'b.txt', 'wheel']))
        for isdir, filename in zip([True, False, False, True], filenames):
            m = Mock()
            type(m).is_dir = PropertyMock(return_value=isdir)
            type(m).filename = PropertyMock(return_value=filename)
            files.append(m)
        mock.return_value = files
        retrieved = self.s.ls('/mybucket/path', dir_only=True)
        mock.assert_called_with('/mybucket/path/', delimiter='/')
        assert len(retrieved) == 2
        assert filenames[0] == retrieved[0]
        assert filenames[3] == retrieved[1]

    @patch('gaepypi.storage.gcs.open')
    def test_open(self, mock):
        self.s.read('/mybucket/path/a.txt')
        mock.assert_called_with('/mybucket/path/a.txt')

    @patch('gaepypi.storage.gcs.open')
    @patch('gaepypi.storage.gcs.RetryParams')
    def test_write(self, retry, open):
        retry.return_value = 'rp'
        m = Mock()
        m.write = Mock()
        open.return_value = m
        self.s.write('/mybucket/path/a.txt', '1111111')
        retry.assert_called_with(backoff_factor=1.1)
        open.assert_called_with('/mybucket/path/a.txt', 'w', options={'x-goog-acl': 'project-private'}, retry_params='rp')
        m.write.assert_called_with('1111111')
