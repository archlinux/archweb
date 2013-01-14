#!/usr/bin/python
import os
import sys
import site

site.addsitedir('/srv/http/archweb-env/lib/python2.7/site-packages')
sys.path.insert(0, "/srv/http/archweb")

os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

os.chdir("/srv/http/archweb")

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
