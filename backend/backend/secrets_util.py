"""Helpers for reading Swarm/Docker secrets from *_FILE or plain environment variables."""

from __future__ import annotations

import os


def load_from_file_or_env(var_name: str) -> str:
    """
    Prefer {var_name}_FILE (path); otherwise read {var_name}.
    Whitespace is stripped (files often end with a newline).
    """
    path = os.environ.get(f"{var_name}_FILE")
    if path:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    if var_name not in os.environ:
        raise KeyError(var_name)
    return os.environ[var_name]


def load_optional_from_file_or_env(var_name: str, default: str = "") -> str:
    """Like load_from_file_or_env but returns default when neither file nor env is set."""
    path = os.environ.get(f"{var_name}_FILE")
    if path:
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    return os.environ.get(var_name, default)
