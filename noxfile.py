import nox


@nox.session(python="2.7")
def default(session):
    session.install('mock', 'pytest', 'gae_installer', 'pyaml', 'webob', 'GoogleAppEngineCloudStorageClient', 'tornado', 'six')

    session.run(
        'pytest',
        'tests/unit'
    )