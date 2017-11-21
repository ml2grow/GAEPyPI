import nox


@nox.session
@nox.parametrize('python_version', ['2.7'])
def default(session, python_version):
    session.interpreter = 'python' + python_version
    session.install('mock', 'pytest', 'gae_installer', 'pyaml', 'webob', 'GoogleAppEngineCloudStorageClient', 'jinja2',
                    'webapp2', 'six')

    session.run(
        'pytest',
        'tests/unit'
    )