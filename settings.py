import os
# Django settings for archweb project.

## Set the debug values
DEBUG = False
TEMPLATE_DEBUG = DEBUG
DEBUG_TOOLBAR = False

## Notification admins
ADMINS = ()

# Set managers to admins
MANAGERS = ADMINS

# Package out-of-date emails for orphans
NOTIFICATIONS = ['arch-notifications@archlinux.org']

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

# Default date format in templates for 'date' filter
DATE_FORMAT = 'Y-m-d'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin_media/'

# Login URL configuration
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Set django's User stuff to use our profile model
AUTH_PROFILE_MODULE = 'main.UserProfile'

# We add a processor to determine if the request is secure or not
TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.contrib.messages.context_processors.messages',
    'main.context_processors.secure',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates".
    # Always use forward slashes, even on Windows.
    '%s/templates' % DEPLOY_PATH,
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.eggs.Loader',
    'django.template.loaders.app_directories.Loader',
)

# This bug is a real bummer:
# http://code.djangoproject.com/ticket/14105
MIDDLEWARE_CLASSES = (
    'main.middleware.UpdateCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
)

ROOT_URLCONF = 'urls'

# Configure where sessions and messages should reside
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'django.contrib.markup',
    'main', # contains shared models and libs
    'mirrors',
    'news',
    'packages',
    'todolists',
    'devel',
    'public',
    'south', # database migration support
)

## Import local settings
from local_settings import *

# Enable caching templates in production environments
if not TEMPLATE_DEBUG:
    TEMPLATE_LOADERS = (
        ('django.template.loaders.cached.Loader', TEMPLATE_LOADERS),
    )

# Enable the debug toolbar if requested
if DEBUG_TOOLBAR:
    MIDDLEWARE_CLASSES = \
            [ 'debug_toolbar.middleware.DebugToolbarMiddleware' ] + \
            list(MIDDLEWARE_CLASSES)

    INSTALLED_APPS = list(INSTALLED_APPS) + [ 'debug_toolbar' ]

# vim: set ts=4 sw=4 et:
