import locale
import os


locale.setlocale(locale.LC_ALL, ("en_US", "UTF-8"))

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DJANGO_DEBUG")
# Helm charts pass "false" instead of Python False, and
# Python "false" is True...
if DEBUG in ["false", "False"]:
    DEBUG = False

# Define the list of allowed hosts to connect to this application
# This is passed in via the environment variable DJANGO_ALLOWED_HOSTS
# which is a string - but ALLOWED_HOSTS requires a list
ALLOWED_HOSTS = list(os.getenv("DJANGO_ALLOWED_HOSTS").split(","))

# Django 4 may require this, at least in our deployment environment.
CSRF_TRUSTED_ORIGINS = list(os.getenv("DJANGO_CSRF_TRUSTED_ORIGINS").split(","))

# Application definition

INSTALLED_APPS = [
    # Enable whitenoise in development per http://whitenoise.evans.io/en/stable/django.html
    "whitenoise.runserver_nostatic",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "terra",
    "crispy_forms",
    "crispy_bootstrap5",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "proj.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "terra.context_processors.add_variable_to_context",
            ]
        },
    }
]

WSGI_APPLICATION = "proj.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": os.getenv("DJANGO_DB_BACKEND"),
        "NAME": os.getenv("DJANGO_DB_NAME"),
        "USER": os.getenv("DJANGO_DB_USER"),
        "PASSWORD": os.getenv("DJANGO_DB_PASSWORD"),
        "HOST": os.getenv("DJANGO_DB_HOST"),
        "PORT": os.getenv("DJANGO_DB_PORT"),
        "TEST": {"NAME": os.getenv("DJANGO_TEST_DB_NAME")},
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Los_Angeles"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# There is a timing issue with Whitenoise that is described here:
# https://github.com/evansd/whitenoise/issues/215
# The work around suggested is to check for the existence of the
# static root directory, and if doesn't exist yet then create it
if not os.path.isdir(STATIC_ROOT):
    os.makedirs(STATIC_ROOT, mode=0o755)

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
    },
}

# Email Configuration
EMAIL_BACKEND = os.getenv("DJANGO_EMAIL_BACKEND")
DEFAULT_FROM_EMAIL = "terra@library.ucla.edu"
if os.getenv("DJANGO_RUN_ENV") != "dev":
    EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST")

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
# Explicitly use AutoField to match the implicit Terra used in earlier Django.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# login redirect
LOGIN_REDIRECT_URL = "/"

INCEPTION_DATE = 2019
