import os
# Django settings for archweb project.

## Import local settings
from local_settings import *

## Set the debug values
TEMPLATE_DEBUG = DEBUG

# Set managers to admins
MANAGERS = ADMINS

# Full path to the data directory
DEPLOY_PATH = os.path.dirname(os.path.realpath(__file__))

# Local time zone for this installation. All choices can be found here:
# http://www.postgresql.org/docs/current/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
TIME_ZONE = 'US/Eastern'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'
DEFAULT_CHARSET = 'utf-8'

SITE_ID = 1

USE_ETAGS = False

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin_media/'

# login url
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
     'django.template.loaders.eggs.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'main.middleware.UpdateCacheMiddleware',
    "django.contrib.sessions.middleware.SessionMiddleware",
    'django.middleware.csrf.CsrfViewMiddleware',
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    'django.middleware.http.ConditionalGetMiddleware',
    "django.middleware.common.CommonMiddleware",
    "django.middleware.doc.XViewMiddleware",
    "main.middleware.AutoUserMiddleware",
    'django.middleware.cache.FetchFromCacheMiddleware',
)

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    '%s/templates' % DEPLOY_PATH,
)

# Set django's User stuff to use our profile model
# format is app.model
AUTH_PROFILE_MODULE = 'main.UserProfile'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'main', # contains shared models and libs
    'mirrors',
    'news',
    'packages',
    'todolists',
    'devel',
    'public',
    'south', # database migration support
)

# vim: set ts=4 sw=4 et:

