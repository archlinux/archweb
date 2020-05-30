# Django settings for archweb project.
from os import path

# Set the debug values
DEBUG = False
DEBUG_TOOLBAR = False

# Notification admins
ADMINS = ()

# Set managers to admins
MANAGERS = ADMINS

# Package out-of-date emails for orphans
NOTIFICATIONS = ['arch-notifications@archlinux.org']

# Full path to the data directory
DEPLOY_PATH = path.dirname(path.realpath(__file__))

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
TIME_ZONE = 'UTC'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'
DEFAULT_CHARSET = 'utf-8'

SITE_ID = 1

# Default date format in templates for 'date' filter
DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i'

# Login URL configuration
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Set django's User stuff to use our profile model
AUTH_PROFILE_MODULE = 'devel.UserProfile'

MIDDLEWARE = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.http.ConditionalGetMiddleware',
    'csp.middleware.CSPMiddleware',
)

# Base of the URL hierarchy
ROOT_URLCONF = 'urls'

# URL to serve static files
STATIC_URL = '/static/'

# Location to collect static files
STATIC_ROOT = path.join(DEPLOY_PATH, 'collected_static')

# Look for more static files in these locations
STATICFILES_DIRS = (
    path.join(DEPLOY_PATH, 'sitestatic'),
)

# Static files backend that allows us to use far future Expires headers
STATICFILES_STORAGE = 'main.storage.MinifiedStaticFilesStorage'

# Configure where messages should reside
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_HTTPONLY = True

# CRSF cookie
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Clickjacking protection
X_FRAME_OPTIONS = 'DENY'

# Referrer Policy
SECURE_REFERRER_POLICY = 'no-referrer-when-downgrade'

# X-Content-Type-Options, stops browsers from trying to MIME-sniff the content type
SECURE_CONTENT_TYPE_NOSNIFF = True

# X-XSS-Protection, enables cross-site scripting filter in most browsers
SECURE_BROWSER_XSS_FILTER = True

# CSP Settings
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'",)
CSP_INCLUDE_NONCE_IN = ['script-src']
CSP_IMG_SRC = ("'self'", 'data:',)
CSP_BASE_URI = ("'none'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)

# Use new test runner
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.sitemaps',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django_countries',
    'django_extensions',

    'main',
    'mirrors',
    'news',
    'packages',
    'planet',
    'todolists',
    'devel',
    'public',
    'releng',
    'visualize',
)

# Logging configuration for not getting overspammed
LOGGING = {
    'version': 1,
    'filters': {
        'ratelimit': {
            '()': 'main.log.RateLimitFilter',
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['ratelimit'],
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        }
    },
}

# Server used for linking to PGP keysearch results
PGP_SERVER = 'sks-keyservers.net'
PGP_SERVER_SECURE = True

# URL for SVN access for fetching commit messages (note absence of packages or
# community bit on the end, repo.svn_root is appended)
SVN_BASE_URL = 'svn://svn.archlinux.org/'

# Trackers used for ISO download magnet links
TORRENT_TRACKERS = (
    'udp://tracker.archlinux.org:6969',
    'http://tracker.archlinux.org:6969/announce',
)

# How long to keep mirrorlog's in days
MIRRORLOG_RETENTION_PERIOD = 365

# Shorten some names just a bit
COUNTRIES_OVERRIDE = {
    'GB': 'United Kingdom',
    'US': 'United States',
}

# Make this unique, and don't share it with anybody.
SECRET_KEY = '00000000000000000000000000000000000000000000000'

# Mailman poster password for announcements
MAILMAN_PASSWORD = ''

DATABASES = {
    'default': {
        'ENGINE':  'django.db.backends.sqlite3',
        'NAME':    'database.db',
    },
}

# Planet limit of items per feed to keep the feed size in check.
RSS_FEED_LIMIT = 25

# Rebuilderd API endpoint
REBUILDERD_URL = 'https://reproducible.archlinux.org/api/v0/pkgs/list'

# Import local settings
try:
    from local_settings import *
except ImportError:
    pass

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            path.join(DEPLOY_PATH, 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.contrib.messages.context_processors.messages',
                'csp.context_processors.nonce',
            ],
        }
    }
]

# Enable the debug toolbar if requested
if DEBUG_TOOLBAR:
    MIDDLEWARE = \
            ['debug_toolbar.middleware.DebugToolbarMiddleware'] + \
            list(MIDDLEWARE)

    INSTALLED_APPS = list(INSTALLED_APPS) + ['debug_toolbar']

# vim: set ts=4 sw=4 et:
