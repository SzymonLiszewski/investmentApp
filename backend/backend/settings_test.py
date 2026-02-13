"""
Django settings for running tests: SQLite in memory (no PostgreSQL required).
Sets required env vars to test defaults before importing main settings.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault("POSTGRES_DB", "")
os.environ.setdefault("POSTGRES_USER", "")
os.environ.setdefault("POSTGRES_PASSWORD", "")
os.environ.setdefault("POSTGRES_HOST", "")
os.environ.setdefault("POSTGRES_PORT", "5432")

from .settings import *

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
