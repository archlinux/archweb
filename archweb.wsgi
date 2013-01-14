#!/usr/bin/python
import os
import sys
import site

base_path = "/srv/http/archweb"

site.addsitedir('/srv/http/archweb-env/lib/python2.7/site-packages')
sys.path.insert(0, base_path)

os.environ['DJANGO_SETTINGS_MODULE'] = "settings"

os.chdir(base_path)

using_newrelic = False
try:
    key_path = os.path.join(base_path, "newrelic.key")
    if os.path.exists(key_path):
        with open(key_path) as keyfile:
            key = keyfile.read().strip()
        os.environ["NEW_RELIC_LICENSE_KEY"] = key

    import newrelic.agent
    from newrelic.api.exceptions import ConfigurationError
    try:
        newrelic.agent.initialize(os.path.join(base_path, "newrelic.ini"))
        using_newrelic = True
    except ConfigurationError:
        pass
except ImportError:
    pass

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()

if using_newrelic:
    application = newrelic.agent.wsgi_application()(application)
