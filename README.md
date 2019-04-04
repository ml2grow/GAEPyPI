# Private package index on Google App Engine
Intended to be used for companies or organizations that need a private PyPi. Originally based on [simplepypi](https://github.com/steiza/simplepypi), however this solution requires a compute engine instance which is quite expensive for the task.

This application runs on Google App Engine (and uses webapp2 instead of tornado) and stores the uploaded packages on Google Cloud Storage. It supports
1. Uploading of packages
2. Downloading by package (or package and version)
3. A / page that is navigatable with a web browser
4. /pypi/ listing
5. Basic ACL through http auth with optional account roles (read/write)
6. Prevent overwriting a package with the same name & version

Unsupported are: 
1. Package registration

## Deploy service
Before deploying, install the required dependencies to the libs folder:
```
pip install -t libs -r requirements-app.txt
```
Next, have a look at config.json, you can set up multiple accounts for the http auth. The passwords are assumed to be hashed with sha1, you can obtain the hash as follows:
```python
from webapp2_extras import security
security.hash_password('password', method='sha1')
```
Now, you are ready to deploy to google app engine. Depending on how you set up your projects, this may require adjusting app.yaml, or setting the right project for gcloud. Then:
```
gcloud app deploy app.yaml
```
will launch your package index

## Uploading packages to the package index
Uploading a python package is quite straightforward. First, add your private package index to `~/.pypirc`:
```
[distutils]
index-servers =
        pypi
        local

[local]
username = username
password = password
repository = https://project.appspot.com

[pypi]
repository=https://pypi.python.org/pypi
username=your_pypi_username
password=your_pypi_password

```
The later reflects a configuration for uploading on the public pypi. Now go to the directory containing setup.py and upload your package to the private package index by specifying the local configuration:
```
python setup.py sdist upload -r local
```

## Installing from the package index
When installing a package (e.g. dummy), specify the url to the package index:
```
pip install -i https://username:password@project.appspot.com/pypi dummy
```

## Running tests
To run the testsuite, we recommend to use the nox tool:
```
pip install nox-automation
```
Next, to run the tests:
```
nox
```