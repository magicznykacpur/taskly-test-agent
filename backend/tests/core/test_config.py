from unittest.mock import patch

import pytest

from app.core.config import resolve_database_url

ENV_VARS = [
    "DATABASE_URL",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "DB_PORT",
    "POSTGRES_DB",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    with patch("app.core.config.load_dotenv"):
        yield


def test_explicit_argument_wins_over_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://env/db")
    assert resolve_database_url("postgresql+psycopg://arg/db") == "postgresql+psycopg://arg/db"


def test_database_url_environment_variable_is_used(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg://env/db")
    assert resolve_database_url() == "postgresql+psycopg://env/db"


def test_url_is_built_from_postgres_variables(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "taskly")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p@ss")
    monkeypatch.setenv("POSTGRES_HOST", "db")
    monkeypatch.setenv("DB_PORT", "5433")
    monkeypatch.setenv("POSTGRES_DB", "tasks")
    assert resolve_database_url() == "postgresql+psycopg://taskly:p%40ss@db:5433/tasks"


def test_missing_postgres_variable_raises_key_error(monkeypatch):
    monkeypatch.setenv("POSTGRES_USER", "taskly")
    with pytest.raises(KeyError):
        resolve_database_url()


def test_dotenv_is_loaded_without_override():
    with patch("app.core.config.load_dotenv") as load:
        resolve_database_url("postgresql+psycopg://arg/db")
    assert load.call_args.kwargs == {"override": False}
