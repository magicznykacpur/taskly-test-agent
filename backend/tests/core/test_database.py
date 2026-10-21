from unittest.mock import Mock, patch

from app.core.database import create_database_engine, create_session_factory, initialize
from app.features.todos.models import Base


def test_engine_uses_the_postgresql_psycopg_driver():
    url = "postgresql+psycopg://taskly:taskly@localhost:5432/taskly"
    engine = create_database_engine(url)
    try:
        assert engine.url.drivername == "postgresql+psycopg"
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
        assert engine.url.database == "taskly"
    finally:
        engine.dispose()


def test_engine_enables_pre_ping():
    engine = create_database_engine("postgresql+psycopg://u:p@localhost:5432/d")
    try:
        assert engine.pool._pre_ping is True
    finally:
        engine.dispose()


def test_session_factory_is_bound_and_does_not_expire_on_commit():
    engine = Mock()
    factory = create_session_factory(engine)
    assert factory.kw["bind"] is engine
    assert factory.kw["expire_on_commit"] is False


def test_initialize_creates_all_tables():
    engine = Mock()
    with patch.object(Base.metadata, "create_all") as create_all:
        initialize(engine)
    create_all.assert_called_once_with(engine)
