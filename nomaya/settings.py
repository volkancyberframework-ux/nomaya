# nomaya/settings.py
from pathlib import Path
import os
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Güvenlik / genel ---
SECRET_KEY = os.environ.get("SECRET_KEY", "django-insecure-@dqu-@telwen(6x(q00gnsg_vk)()r&+atofj-6yyjqopy!s9+")
DEBUG = os.environ.get("DEBUG", "1") == "1"   # local: 1, prod: 0

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")
CSRF_TRUSTED_ORIGINS = [
    "https://*.onrender.com",
    "https://nomaya.co",
]

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

# --- Statik / medya ---
STATIC_URL = "/static/"
# Projedeki kaynak statikler (ör. BASE_DIR/static)
STATICFILES_DIRS = [BASE_DIR / "static"]
# collectstatic çıktısı (Render servisleyecek klasör)
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise manifest + sıkıştırma
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
WHITENOISE_MANIFEST_STRICT = False  # eksik referanslarda hata atma

MEDIA_URL = "/media/"
MEDIA_ROOT = '/data/media'

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

# --- Prod güvenlik (DEBUG=0 iken önerilir) ---
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = False  # Render TLS terminates; istersen True yap
