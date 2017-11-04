import os
import cgi
import webapp2
import cloudstorage as gcs
from decorators import basic_auth
from google.appengine.api import app_identity

# Standard setup
BUCKET_NAME = os.environ.get('BUCKET_NAME', app_identity.get_default_gcs_bucket_name())
my_default_retry_params = gcs.RetryParams(initial_delay=0.2,
                                          max_delay=5.0,
                                          backoff_factor=2,
                                          max_retry_period=15)
gcs.set_default_retry_params(my_default_retry_params)


class BaseHandler(webapp2.RequestHandler):

    def write404(self):
        self.response.set_status(404)
        self.response.write(
            '<html><head><title>404 Not Found</title></head><body>'
            '<h1>Not found</h1></body></html>'
        )

    def get_package_path(self, package, version=None, want_file=False):
        path = '/{0}/packages/{1}/'.format(BUCKET_NAME, package)

        if version:
            path = '{0}{1}'.format(path, version)

            if want_file:
                path = '{0}/{1}'.format(path, '{}-{}.tar.gz'.format(package, version))

        return path

    def generate_package_link(self, package_link):
        path_split = [cgi.escape(pe) for pe in package_link.split('/')]
        fname = '{package}-{version}.tar.gz'.format(package=path_split[-3], version=path_split[-2])
        return '<a href="{0}/{1}">{1}</a><br />'.format('/'.join(path_split[0:1] + path_split[2:-1]), fname)


# Handlers
class IndexHandler(BaseHandler):

    @basic_auth
    def get(self):
        self.response.write(
            '<html><head><title>gaepypi</title></head><body>'
            '<a href="/packages">packages</a></body></html>'
            )

    @basic_auth
    def post(self):
        name = self.request.get('name', default_value=None)
        version = self.request.get('version', default_value=None)
        action = self.request.get(':action', default_value=None)
        content = self.request.POST.getall('content')[0].file.read()

        if name and version and content and action == 'file_upload':
            name = name.lower()
            path = self.get_package_path(name, version, want_file=True)

            # Write file in bucket
            write_retry_params = gcs.RetryParams(backoff_factor=1.1)
            gcs_file = gcs.open(path, 'w', options={}, retry_params=write_retry_params)
            gcs_file.write(content)
            gcs_file.close()


class PypiHandler(BaseHandler):

    @basic_auth
    def get(self):
        self.response.write('<html><body>\n')
        packages_path = '/{0}/packages/'.format(BUCKET_NAME)
        for package in gcs.listbucket(packages_path, delimiter='/'):
            if package.is_dir:
                vl = [version.filename for version in gcs.listbucket(package.filename, delimiter='/') if version.is_dir]
                vl.sort()

                if len(vl) > 0:
                    self.response.write(self.generate_package_link(vl[-1]))

        self.response.write('</body></html>')


class PypiPackageHandler(BaseHandler):

    @basic_auth
    def get(self, package):
        package = package.lower()
        package_path = self.get_package_path(package)
        contents = list(gcs.listbucket(package_path, delimiter='/'))
        vl = [version.filename for version in contents if version.is_dir]
        vl.sort()

        if len(vl) == 0:
            self.write404()
            return

        self.response.write('<html><body>{}</body></html>'.format(self.generate_package_link(vl[-1])))


class PypiPackageVersionHandler(BaseHandler):

    @basic_auth
    def get(self, package, version):
        package = package.lower()
        path = self.get_package_path(package, version, want_file=True)

        try:
            gcs.stat(path)
            self.response.write('<html><body>{}</body></html>'.format(self.generate_package_link(path)))
        except gcs.NotFoundError:
            self.write404()


class PackageBase(BaseHandler):

    @basic_auth
    def get(self):
        package_path = '/{0}/packages/'.format(BUCKET_NAME)
        contents = list(gcs.listbucket(package_path, delimiter='/'))
        contents.sort()

        self.response.write('<html><body>\n')

        for each in contents:
            name = each.filename.split('/')[-2]
            self.response.write('<a href="/packages/{each}">{each}</a><br />'.format(each=cgi.escape(name),))

        if len(contents) == 0:
            self.response.write('Nothing to see here yet, try uploading a package!')

        self.response.write('</body></html>\n')


class PackageList(BaseHandler):

    @basic_auth
    def get(self, package):
        package = package.lower()
        package_path = self.get_package_path(package)
        contents = list(gcs.listbucket(package_path, delimiter='/'))
        versions = [version.filename for version in contents if version.is_dir]
        versions.sort()

        if len(versions) == 0:
            self.write404(self)
            return

        self.response.write('<html><body>\n')

        for each_version in versions:
            self.response.write(self.generate_package_link(each_version))

        self.response.write('</body></html>\n')


class PackageDownload(BaseHandler):

    @basic_auth
    def get(self, name, version, _):
        path = self.get_package_path(name, version, want_file=True)

        self.response.content_type = 'application/octet-stream'
        self.response.headers.add('Content-Disposition', 'attachment; filename={0}'.format(path.split('/')[-1]))

        gcs_file = gcs.open(path)
        self.response.write(gcs_file.read())
        gcs_file.close()


__all__ = [cls.__name__ for cls in BaseHandler.__subclasses__()]
