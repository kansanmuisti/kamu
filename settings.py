# Django settings for kamu project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

#DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
#DATABASE_NAME = os.path.join(os.path.dirname(__file__), 'kamu.db')

DATABASE_ENGINE = 'mysql'
DATABASE_NAME = 'kamu'
DATABASE_USER = 'kamu'
DATABASE_PASSWORD = 'kamu'
DATABASE_HOST = ''
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

DJAPIAN_DATABASE_PATH = os.path.dirname(__file__) + '/djapian/'

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Helsinki'

# Language code for this installation. All choices can be found here:
LANGUAGES_EXT=(('en', 'English', 'in English'),
               ('fi', 'Finnish', 'suomeksi'))
LANGUAGES=[(l[0], l[1]) for l in LANGUAGES_EXT]

# http://www.i18nguy.com/unicode/language-identifiers.html
#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'fi'
DJAPIAN_STEMMING_LANG = 'fi'
DATE_FORMAT = 'd.m.Y'
TIME_FORMAT = 'H:i'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.dirname(__file__) + '/static/'
MEDIA_TMP_DIR = 'tmp/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/static/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ljqf))w56l68l26zgtn**2u198y0j5$82o^ac%m0x23l=hq_75'

INTERNAL_IPS = ( '127.0.0.1', )

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'facebook.context_processors.facebook',
    'i18n.context_processors.other_languages',
)


MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'i18n.middleware.SetDefaultLanguageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'httpstatus.middleware.HttpStatusErrorsMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'kamu.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(os.path.dirname(__file__), 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'django.contrib.webdesign',
    'django.contrib.markup',
    'django.contrib.messages',
    'django_extensions',
    'lifestream',
    'sorl.thumbnail',
    'kamu.votes',
    'kamu.users',
    'kamu.orgs',
    'kamu.comments',
    'tagging',
    'djapian',
    'facebook',
    'registration',
    'cms',
    'user_voting',
    'opinions',
)

AUTH_PROFILE_MODULE="kamu.users.KamuProfile"
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'kamu.facebook.auth_backends.FacebookBackend',
)

# Activation window from the sending of the activation e-mail
ACCOUNT_ACTIVATION_DAYS = 3
# URL for redirection when the user needs to login and nothing
# else is specified in the code, like when using pre-canned
# functionality in django-register
LOGIN_URL = '/account/login/'
DEFAULT_FROM_EMAIL = 'Kansan muisti <noreply@kansanmuisti.fi>'
SERVER_EMAIL = 'noreply@kansanmuisti.fi'

COMMENTS_APP = 'kamu.comments'
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

FACEBOOK_ENABLED = False
FACEBOOK_APP_ID = "Set this in settings_local"
FACEBOOK_APP_SECRET = "Set this in settings_local"
# Optional
FACEBOOK_DOMAIN = None

try:
    from settings_local import *
except ImportError:
    pass
