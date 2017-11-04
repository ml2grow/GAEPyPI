import base64
import json
from webapp2_extras import security


def basic_auth(func):
    def callf(handler, *args, **kwargs):
        auth_header = handler.request.headers.get('Authorization')
        if auth_header is None:
            __basic_login(handler)
        else:
            (username, password) = base64.b64decode(auth_header.split(' ')[1]).split(':')
            if __basic_lookup(username) == __basic_hash(password):
                return func(handler, *args, **kwargs)
            else:
                __basic_login(handler)

    return callf


def __basic_login(handler):
    handler.response.set_status(401, message="Authorization Required")
    handler.response.headers['WWW-Authenticate'] = 'Basic realm="Secure Area"'


def __basic_lookup(username):
    with open('config.json') as data_file:
        config = json.load(data_file)
    for account in config["accounts"]:
        if account['username'] == username:
            return account['password']


def __basic_hash(password):
    return security.hash_password(password, method='sha1')
