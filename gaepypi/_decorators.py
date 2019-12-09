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


def basic_auth(required_roles=None):
    """
    Decorator to require HTTP auth for request handler
    """
    def decorator_basic_auth(func):
        @wraps(func)
        def callf(handler, *args, **kwargs):
            auth_header = handler.request.headers.get('Authorization')
            if auth_header is None:
                return __basic_login(handler)
            if not auth_header.startswith('Basic '):
                return __basic_login(handler)

            (username, password) = base64.b64decode(auth_header.split(' ')[1]).split(':')
            account = __basic_lookup(username)

            # Return 401 Unauthorized if user did not specify credentials or password is mismatched
            if not account or account["password"] != __basic_hash(password):
                return __basic_login(handler)

            # Return 403 Forbidden if user's account does not have any of the required access roles
            user_roles = account['roles'] if 'roles' in account else []
            if required_roles and any([(required_role not in user_roles) for required_role in required_roles]):
                return __basic_forbidden(handler)

            return func(handler, *args, **kwargs)
        return callf
    return decorator_basic_auth


def __basic_login(handler):
    handler.set_header('WWW-Authenticate', 'Basic realm="Secure Area"')
    handler.set_status(401)
    handler.finish()
    return False


def __basic_hash(password):
    return sha1(password.encode('utf-8')).hexdigest()


def __basic_lookup(username):
    with open('config.json') as data_file:
        config = json.load(data_file)
    return config["accounts"].get(username, None)


def __basic_forbidden(handler):
    handler.set_status(403, message="Forbidden")


