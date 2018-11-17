# Django settings for kamu project.
import os
import sys
import json

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True
TEMPLATE_DEBUG = DEBUG
JS_DEBUG = False

COMPRESS_ENABLED = True

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS
# This is used at least for new supporting members
NOTIFICATIONS = ADMINS

ENVELOPE_USE_HTML_EMAIL = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'kamu',
        'USER': 'kamu',
        'PASSWORD': 'kamu',
        # Keep the database connection open for an hour
        #'CONN_MAX_AGE': 3600,
    }
}

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

LOCALE_PATHS = [
    BASE_DIR + '/locale'
]

# http://www.i18nguy.com/unicode/language-identifiers.html
#LANGUAGE_CODE = 'en-us'
LANGUAGE_CODE = 'fi'
DATE_FORMAT = 'd.m.Y'
TIME_FORMAT = 'H:i'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True
USE_L10N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.dirname(__file__) + '/media/'
MEDIA_TMP_DIR = 'tmp/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.dirname(__file__) + '/static/'
STATIC_URL = '/static/'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/less', 'lessc {infile} {outfile}'),
    ('text/coffeescript', 'coffee --compile --stdio'),
)
COMPRESS_JS_FILTERS = []

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ljqf))w56l68l26zgtn**2u198y0j5$82o^ac%m0x23l=hq_75'

INTERNAL_IPS = ('127.0.0.1',)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'kamu-cache',
    }
}


def read_config(name):
    f = open(os.path.join(BASE_DIR, 'elasticsearch/{}.json'.format(name)))
    return json.load(f)

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'multilingual_haystack.custom_elasticsearch_search_backend.CustomEsSearchEngine',
        'URL': 'http://localhost:9200/',
        'INDEX_NAME': 'kamu',
        'MAPPINGS': read_config('mappings_finnish')['modelresult']['properties'],
        'SETTINGS': read_config('settings_finnish'),
        'TIMEOUT': 120,
        'BATCH_SIZE': 1000,
    }
}

HAYSTACK_LIMIT_TO_REGISTERED_MODELS = False


SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# List of callables that know how to import templates from various sources.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "parliament.views.kamu_context_processor",
            ],
        },
    },
]
print(TEMPLATES[0]['DIRS'])

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'httpstatus.middleware.HttpStatusErrorsMiddleware',
    # ProfilerMiddleware needs to be last
    #'profiler.middleware.ProfilerMiddleware',
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
)

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    #'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    #'django.contrib.admin',
    #'debug_toolbar.apps.DebugToolbarConfig',
    'django_extensions',

    'sorl.thumbnail',
    'compressor',
    'tastypie',
    'haystack',
    'corsheaders',
    'envelope',

    'social',
    'parliament',
    'eduskunta',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Activation window from the sending of the activation e-mail
ACCOUNT_ACTIVATION_DAYS = 3
# URL for redirection when the user needs to login and nothing
# else is specified in the code, like when using pre-canned
# functionality in django-register
LOGIN_URL = '/account/login/'
DEFAULT_FROM_EMAIL = 'Kansan muisti <noreply@kansanmuisti.fi>'
SERVER_EMAIL = 'noreply@kansanmuisti.fi'

CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = ['GET']

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

TASTYPIE_DEFAULT_FORMATS = ['json']

FACEBOOK_ENABLED = False
FACEBOOK_APP_ID = "Set this in settings_local"
FACEBOOK_APP_SECRET = "Set this in settings_local"
# Optional
FACEBOOK_DOMAIN = None

KAMU_OPINIONS_MAGIC_USER = 'kamu'

FAST_TEST = False

NUMBER_OF_MPS = 200


# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
f = os.path.join(BASE_DIR, "local_settings.py")
if os.path.exists(f):
    import sys
    import imp
    module_name = "%s.local_settings" % ROOT_URLCONF.split('.')[0]
    module = imp.new_module(module_name)
    module.__file__ = f
    sys.modules[module_name] = module
    exec(open(f, "rb").read())
