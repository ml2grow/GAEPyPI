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
from webapp2_extras import security


def basic_auth(required_roles=None):
    """
    Decorator to require HTTP auth for request handler
    """
    def decorator_basic_auth(func, *args, **kwargs):
        def callf(handler):
            auth_header = handler.request.headers.get('Authorization')
            if auth_header is None:
                __basic_login(handler)
            else:
                parts = base64.b64decode(auth_header.split(' ')[1]).split(':')
                username = parts[0]
                password = ':'.join(parts[1:])
                account = __basic_lookup(username)

                # Return 401 Unauthorized if user did not specify credentials or password is mismatched
                if not account or account["password"] != __basic_hash(password):
                    return __basic_login(handler)

                # Return 403 Forbidden if user's account does not have any of the required access roles
                user_roles = account['roles'] if 'roles' in account else []
                if required_roles and any([(required_role not in user_roles) for required_role in required_roles]):
                    return __basic_forbidden(handler)

                else:
                    return func(handler, *args, **kwargs)

        return callf
    return decorator_basic_auth


def __basic_login(handler):
    handler.response.set_status(401, message="Authorization Required")
    handler.response.headers['WWW-Authenticate'] = 'Basic realm="Secure Area"'


def __basic_forbidden(handler):
    handler.response.set_status(403, message="Forbidden")


def __basic_lookup(username):
    with open('config.json') as data_file:
        config = json.load(data_file)
    for account in config["accounts"]:
        if account['username'] == username:
            return account


def __basic_hash(password):
    return security.hash_password(password, method='sha1')
