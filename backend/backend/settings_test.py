"""
Django settings for running tests: SQLite in memory (no PostgreSQL required).
Import all from main settings and override only DATABASES.
"""
from .settings import * 

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
