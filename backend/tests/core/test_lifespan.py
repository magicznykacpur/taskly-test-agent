import asyncio
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.lifespan import lifespan


def _app():
    return SimpleNamespace(state=SimpleNamespace(database_url="postgresql+psycopg://x/y"))


def _run(app, body=None):
    async def go():
        async with lifespan(app):
            if body:
                body()

    asyncio.run(go())


def test_lifespan_sets_up_session_factory_and_disposes_engine():
    app = _app()
    seen = {}
    with patch("app.core.lifespan.create_database_engine") as create_engine, \
         patch("app.core.lifespan.initialize") as init, \
         patch("app.core.lifespan.create_session_factory") as create_factory:
        _run(app, lambda: seen.update(factory=app.state.session_factory))
    engine = create_engine.return_value
    create_engine.assert_called_once_with("postgresql+psycopg://x/y")
    init.assert_called_once_with(engine)
    create_factory.assert_called_once_with(engine)
    assert seen["factory"] is create_factory.return_value
    engine.dispose.assert_called_once_with()


def test_lifespan_disposes_engine_when_initialize_fails():
    with patch("app.core.lifespan.create_database_engine") as create_engine, \
         patch("app.core.lifespan.initialize", side_effect=RuntimeError("no db")):
        with pytest.raises(RuntimeError, match="no db"):
            _run(_app())
    create_engine.return_value.dispose.assert_called_once_with()
