# Django settings for murmur project.

import os
import django


DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))

_ENV_FILE_PATH = '/opt/murmur/env'
_DEBUG_FILE_PATH = '/opt/murmur/debug'
_WEBSITE_FILE_PATH = '/opt/murmur/website'

def _get_env():
    f = open(_ENV_FILE_PATH)
    env = f.read()

    if env[-1] == '\n':
        env = env[:-1]
    
    f.close()
    return env
ENV = _get_env() 

def _get_debug():
    f = open(_DEBUG_FILE_PATH)
    debug = f.read()

    if debug[-1] == '\n':
        debug = debug[:-1]
    
    f.close()
    if debug == 'true':
        return True
    else:
        return False
    
DEBUG = _get_debug()

def _get_website():
    f = open(_WEBSITE_FILE_PATH)
    website = f.read()

    if website[-1] == '\n':
        website = website[:-1]
    
    f.close()
    return website
    
WEBSITE = _get_website()

try:
    execfile(SITE_ROOT + '/../private.py')
except IOError:
    print "Unable to open configuration file!"

if ENV == 'prod':
    if WEBSITE == 'murmur':
        BASE_URL = 'murmur.csail.mit.edu'
    else:
        BASE_URL = 'squadbox.csail.mit.edu'
    MYSQL = MYSQL_PROD
elif ENV == 'staging':
    BASE_URL = 'murmur-dev.csail.mit.edu'
    MYSQL = MYSQL_DEV
else:
    BASE_URL = 'localhost:8000'
    MYSQL = MYSQL_LOCAL

TEMPLATE_DEBUG = DEBUG

LOGIN_REDIRECT_URL = "/"

EMAIL_HOST = 'localhost'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_EMAIL = 'no-reply@' + BASE_URL
DEFAULT_FROM_EMAIL = DEFAULT_EMAIL


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': MYSQL["NAME"],# Or path to database file if using sqlite3.
        'USER': MYSQL["USER"], # Not used with sqlite3.
        'PASSWORD': MYSQL["PASSWORD"],# Not used with sqlite3.
        'HOST': MYSQL["HOST"], # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '', # Set to empty string for default. Not used with sqlite3.
        'STORAGE_ENGINE': 'MyISAM',
        'OPTIONS': {'charset': 'utf8mb4'},
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)



# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',

    'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'fr&amp;qg*+c!z6q_^v6o1kzd6lxj-3m3q-=oku8f52*c+@)+1hnx+'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django_mobile.loader.Loader',
    
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django_mobile.context_processors.flavour',
    
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'django_mobile.middleware.MobileDetectionMiddleware',
    'django_mobile.middleware.SetFlavourMiddleware',
    
)

ROOT_URLCONF = 'http_handler.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'http_handler.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# one week activation window after a user signs up for an account
ACCOUNT_ACTIVATION_DAYS = 7

LOGIN_REDIRECT_URL = "/"

AUTH_USER_MODEL = 'schema.UserProfile'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    # 'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    
    #our apps
    'http_handler',
    'schema',
    'browser',
    'smtp_handler',
    'gmail_setup',
    
    #third party apps
    'registration',
    'south',
    'django_mobile',
    'storages'
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    # custom formatters used to describe the logs
    'formatters': {
        # this formatter just includes the message
        'custom.brief' : {
            'format': '%(message)s'
        },
        # this formatter is for the user
        'custom.user' : {
            'format': '%(asctime)s %(levelname)-8s %(funcName)s %(message)s'
        },
        # this formatter includes the time, log level, logger name, and message
        'custom.precise' : {
            'format' : '%(asctime)s %(levelname)-8s %(name)-15s %(message)s',
            'datefmt' : '%Y-%m-%d %H:%M:%S''format'
        },
        # this formatter includes file name and line number info
        'custom.debug': {
            'format': '%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        # this handler logs to a file
        'custom.file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            # TODO change this to relative path
            'filename': '/home/ubuntu/murmur/logs/murmur.log',
            'formatter': 'custom.debug'
        }
    },
    'loggers': {
        'murmur': {
            'handlers': ['custom.file'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },

        # comment this out if you want to see DB queries in logs
        'django.db.backends': {
            'handlers': None, 
            'propagate': False,
            'level':'DEBUG',
        },
    }
}

# celery settings
try:
        from celeryconfig import *
except ImportError:
        pass



# local Settings - overriden by local_settings.py
try:
        from local_settings import *
except ImportError:
        pass

# Storage for attachments
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
AWS_DEFAULT_ACL = 'private'