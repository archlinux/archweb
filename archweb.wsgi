#!/usr/bin/python
import os
import sys
import site

base_path = "/srv/http/archweb"

site.addsitedir('/srv/http/archweb-env/lib/python3.6/site-packages')
sys.path.insert(0, base_path)

os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

os.chdir(base_path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
