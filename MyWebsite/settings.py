"""Shared Django configuration for local development and production."""

from ipaddress import ip_address
from pathlib import Path

from decouple import config
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Local development works without deployment credentials. The production image
# explicitly sets DEBUG=False, which requires a private secret and host allowlist.
DEBUG = config("DEBUG", default=True, cast=bool)
SECRET_KEY = config("SECRET_KEY", default="django-insecure-local-development-only")


def env_list(name, default=""):
    return config(name, default=default).replace(",", " ").split()


ALLOWED_HOSTS = env_list(
    "DJANGO_ALLOWED_HOSTS",
    default="localhost 127.0.0.1 [::1]" if DEBUG else "",
)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

if not DEBUG:
    if len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith("django-insecure-"):
        raise ImproperlyConfigured("Set a private SECRET_KEY of at least 50 characters in production.")
    if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS:
        raise ImproperlyConfigured("Set DJANGO_ALLOWED_HOSTS to the site's hostnames in production.")

# The first middleware discards this header from all other peers. Only the
# gateway and in-container healthcheck need trust; application ports stay private.
DJANGO_TRUST_PROXY = config("DJANGO_TRUST_PROXY", default=False, cast=bool)
DJANGO_TRUSTED_PROXY_IPS = env_list("DJANGO_TRUSTED_PROXY_IPS")
try:
    for address in DJANGO_TRUSTED_PROXY_IPS:
        ip_address(address)
except ValueError as error:
    raise ImproperlyConfigured("DJANGO_TRUSTED_PROXY_IPS must contain exact IP addresses.") from error
if DJANGO_TRUST_PROXY:
    if not DJANGO_TRUSTED_PROXY_IPS:
        raise ImproperlyConfigured("Set DJANGO_TRUSTED_PROXY_IPS when trusting proxy headers.")
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = config("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG, cast=bool)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = config("DJANGO_SECURE_HSTS_SECONDS", default=0 if DEBUG else 3600, cast=int)
# Keep HSTS scoped to this hostname; other subdomains may host separate services.
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False


# Application definition

INSTALLED_APPS = [
    'myapp.apps.MyappConfig',
    'rootPage.apps.RootpageConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'MyWebsite.middleware.TrustedProxyHeadersMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'MyWebsite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'MyWebsite.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': Path(config('DJANGO_DB_PATH', default=str(BASE_DIR / 'db.sqlite3'))),
        'OPTIONS': {'timeout': 20},
    }
}

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

# Installed apps expose their own static directories automatically.
STATICFILES_DIRS = [BASE_DIR / "physGenViewer" / "static"]
STATIC_ROOT = Path(config("DJANGO_STATIC_ROOT", default=str(BASE_DIR / "staticfiles")))
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}

# Default primary key field type

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
