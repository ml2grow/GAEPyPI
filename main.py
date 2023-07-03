import os

from flask import Flask, request, abort, send_file
from google.cloud.exceptions import NotFound

from gaepypi import Package, GCStorage, GAEPyPIError, PackageIndex
from gaepypi._decorators import basic_auth
from google.appengine.api import app_identity, wrap_wsgi_app

app = Flask(__name__)
app.wsgi_app = wrap_wsgi_app(app.wsgi_app)
storage = None


def get_storage():
	global storage
	if not storage:
		bucket_name = os.environ.get('BUCKET_NAME')
		if not bucket_name:
			bucket_name = app_identity.get_default_gcs_bucket_name()
		storage = GCStorage(bucket_name)
	return storage


@app.route("/")
@basic_auth()
def root():
	return '<a href="/packages">packages</a>'


@app.route("/pypi/")
@basic_auth()
def root_pypi():
	return get_storage().to_html(full_index=True)


@app.route("/", methods=['POST'])
@basic_auth(required_roles=['write'])
def root_post():
	name = request.values.get('name')
	version = request.values.get('version')
	action = request.values.get(':action')

	if name and version and len(request.files) and action == 'file_upload':
		try:
			upload = request.files['content']
			filename = upload.filename
			package = Package(get_storage(), name, version)
			package.put_file(filename, upload.stream)
		except GAEPyPIError as e:
			abort(403)
	return ""


@app.route("/packages", methods=['GET'])
@basic_auth()
def packages_get():
	storage = get_storage()
	if storage.empty():
		return 'Nothing to see here yet, try uploading a package!'
	else:
		return storage.to_html(full_index=False)


@app.route("/packages/<package>", methods=['GET'])
@basic_auth()
def packages_get_package(package):
	index = PackageIndex(get_storage(), package)
	if index.exists():
		return index.to_html(full_index=False)
	abort(404)


@app.route("/packages/<package>/<version>", methods=['GET'])
@app.route("/pypi/package/<package>/<version>", methods=['GET'])
@basic_auth()
def get(package, version):
	package = Package(get_storage(), package, version)
	if package.exists():
		return package.to_html()
	abort(404)


@app.route("/packages/<name>/<version>/<filename>", methods=['GET'])
@basic_auth()
def package_download(name, version, filename):
	try:
		package = Package(get_storage(), name, version)
		gcs_file = package.get_file(filename)
		return send_file(gcs_file, mimetype='application/octet-stream', as_attachment=True, download_name=filename)
	except NotFound:
		abort(404)


@app.route("/pypi/package/<path:package>", methods=['GET'])
@basic_auth()
def pypi_package_get(package):
	storage = get_storage()
	index = PackageIndex(storage, package)
	if not index.empty() and index.exists(storage):
		return index.to_html(full_index=True)
	abort(404)


if __name__ == "__main__":
	# This is used when running locally only. When deploying to Google App
	# Engine, a webserver process such as Gunicorn will serve the app. This
	# can be configured by adding an `entrypoint` to app.yaml.
	# Flask's development server will automatically serve static files in
	# the "static" directory. See:
	# http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
	# App Engine itself will serve those files as configured in app.yaml.
	app.run(host="127.0.0.1", port=8080, debug=True)
