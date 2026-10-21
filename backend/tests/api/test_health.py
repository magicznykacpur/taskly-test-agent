from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
from app.api.health import router


def _client(repository):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_repository] = lambda: repository
    return TestClient(app, raise_server_exceptions=False)


def test_health_returns_ok_and_queries_the_database():
    repository = Mock()
    response = _client(repository).get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    repository.session.execute.assert_called_once()


def test_health_fails_when_database_is_unreachable():
    repository = Mock()
    repository.session.execute.side_effect = RuntimeError("db down")
    response = _client(repository).get("/api/health")
    assert response.status_code == 500
