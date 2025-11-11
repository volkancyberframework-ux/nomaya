# nomaya/settings.py
from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Güvenlik / genel ---
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-@dqu-@telwen(6x(q00gnsg_vk)()r&+atofj-6yyjqopy!s9+")
DEBUG = True   # local: 1, prod: 0

ALLOWED_HOSTS = ["nomaya.co", "www.nomaya.co", "nomaya.onrender.com"]

CSRF_TRUSTED_ORIGINS = [
    "https://nomaya.co",
    "https://www.nomaya.co",
]
SECURE_SSL_REDIRECT = True           # Render’da HTTPS aktifse güzel olur
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True


# --- Auth yönlendirmeleri ---
LOGIN_URL = "sign_in"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "sign_in"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "adminsortable2",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # ✅ WhiteNoise tam burada olmalı
    "whitenoise.middleware.WhiteNoiseMiddleware",

    "django.contrib.sessions.middleware.SessionMiddleware",
    # ✅ Türkçe/yerelleştirme için gerekli
    "django.middleware.locale.LocaleMiddleware",

    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "nomaya.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "nomaya.wsgi.application"

# --- Veritabanı ---
DATABASES = {
    "default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=600)
}

# --- Static ---
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

# Use WhiteNoise’s compressed manifest storage (better than Django’s default)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# --- Media (persistent) ---
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "/data/media"))  # uses /data on Render


# Paket statiklerini de bulabilelim (çoğu projede default zaten bunlar)
STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

# --- Parola doğrulayıcıları ---
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- Uluslararasılaştırma (TR tarih/ay/gün) ---
LANGUAGE_CODE = "tr"
TIME_ZONE = "Europe/Istanbul"
USE_I18N = True
USE_TZ = True

# (İsteğe bağlı) Desteklenen diller ve locale klasörü:
LANGUAGES = [
    ("tr", "Türkçe"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
