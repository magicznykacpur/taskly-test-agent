from unittest.mock import patch

from fastapi.testclient import TestClient

from app.factory import create_app


def test_create_app_stores_resolved_database_url():
    with patch("app.factory.resolve_database_url", return_value="resolved") as resolve:
        app = create_app("explicit")
    resolve.assert_called_once_with("explicit")
    assert app.state.database_url == "resolved"
    assert app.title == "Taskly API"


def test_create_app_registers_health_and_todo_routes():
    with patch("app.factory.resolve_database_url", return_value="resolved"):
        paths = set(create_app().openapi()["paths"])
    assert {"/api/health", "/api/todos"} <= paths


def test_app_startup_wires_session_factory_and_disposes_engine():
    with patch("app.factory.resolve_database_url", return_value="sqlite://"), \
         patch("app.core.lifespan.create_database_engine") as create_engine, \
         patch("app.core.lifespan.initialize"), \
         patch("app.core.lifespan.create_session_factory") as create_factory:
        app = create_app()
        with TestClient(app):
            assert app.state.session_factory is create_factory.return_value
    create_engine.return_value.dispose.assert_called_once_with()
