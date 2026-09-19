"""
Django settings for running the app under Playwright e2e tests.

File-based SQLite and mock data fetchers (no external API keys
needed, deterministic responses).
"""
import os
import tempfile

os.environ.setdefault("SECRET_KEY", "e2e-secret-key-not-for-production")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("ALLOWED_HOSTS", "localhost,127.0.0.1")
os.environ.setdefault("POSTGRES_DB", "")
os.environ.setdefault("POSTGRES_USER", "")
os.environ.setdefault("POSTGRES_PASSWORD", "")
os.environ.setdefault("POSTGRES_HOST", "")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("USE_MOCK_DATA_FETCHER", "true")

from .settings import *  

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(tempfile.gettempdir(), "captrivio_e2e.sqlite3"),
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_BROKER_URL = "memory://"

ML_MODELS_DIR = tempfile.mkdtemp(prefix="e2e_ml_models_")
