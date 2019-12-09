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

import base64
import json
from functools import wraps
from hashlib import sha1


def basic_auth(f):
    @wraps(f)
    def new_f(*args):
        handler = args[0]

        auth_header = handler.request.headers.get('Authorization')
        if auth_header is None:
            return __basic_login(handler)
        if not auth_header.startswith('Basic '):
            return __basic_login(handler)

        (username, password) = base64.b64decode(auth_header.split(' ')[1]).split(':')

        if auth(username, password):
            f(*args)
        else:
            __basic_login(handler)

    return new_f



def __basic_login(handler):
    handler.set_header('WWW-Authenticate', 'Basic realm="Secure Area"')
    handler.set_status(401)
    handler.finish()
    return False


def auth(username, password):
    with open('config.json') as data_file:
        config = json.load(data_file)

    if username in config["accounts"]:
        account = config["accounts"][username]
        return account["password"] == sha1(password.encode('utf-8')).hexdigest()

    return False
