"""
Django settings for running tests uses SQLite in memory (no SQL Server required).
Import all from main settings and override only DATABASES.
"""
from .settings import * 

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
