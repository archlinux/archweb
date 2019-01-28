#!/usr/bin/python
import os
import sys
import site

base_path = "/srv/http/archweb"
py_version = sys.version_info

site.addsitedir('/srv/http/archweb-env/lib/python{}.{}/site-packages'.format(py_version.major, py_version.minor))
sys.path.insert(0, base_path)

os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

os.chdir(base_path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
