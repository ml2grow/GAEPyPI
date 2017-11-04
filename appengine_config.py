import os
from google.appengine.ext import vendor

lib_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'libs')
vendor.add(lib_path)
