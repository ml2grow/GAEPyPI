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

import json
import hashlib
from flask import Flask, Response, request


def load_accounts():
	ret = {}
	with open('config.json') as data_file:
		config = json.load(data_file)
	for account in config["accounts"]:
		ret[account['username']] = account
	return ret


account_by_name = load_accounts()


def __basic_hash(password):
	m = hashlib.sha1()
	m.update(password.encode('utf-8'))
	return m.hexdigest()


def valid_credentials(username, password, required_roles=None):
	account = account_by_name.get(username)
	if not account or account["password"] != __basic_hash(password):
		return False
	user_roles = account.get('roles', [])
	if required_roles and any([(required_role not in user_roles) for required_role in required_roles]):
		return False
	return True


def basic_auth(required_roles=None):
	def inner_decorator(f):
		def wrapped(*args, **kwargs):
			auth = request.authorization
			if not auth or not auth.username or not auth.password:
				return Response('Login!', 401, {'WWW-Authenticate': 'Basic realm="Secure Area"'})
			if not valid_credentials(auth.username, auth.password, required_roles):
				return Response('Forbidden', 403)
			return f(*args, **kwargs)
		wrapped.__name__ = f.__name__
		return wrapped
	return inner_decorator

