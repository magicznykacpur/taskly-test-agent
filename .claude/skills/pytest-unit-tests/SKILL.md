---
name: pytest-unit-tests
description: Conventions and patterns for writing pytest unit tests for the FastAPI + SQLAlchemy backend in backend/. Use when creating or updating any file under backend/tests.
---

# Backend unit tests (pytest)

The backend is `backend/app` (FastAPI routers, a SQLAlchemy repository, pydantic schemas and validators). Tests live in `backend/tests`, mirroring the `app` package: `app/features/todos/router.py` is tested in `tests/features/todos/test_router.py`. Every test directory needs an `__init__.py`.

## Ground rules

- **No real database.** Unit tests never connect to Postgres. Use the mocks below.
- Plain functions named `test_<behaviour>`, no test classes. Name the behaviour, for example `test_update_returns_404_when_task_is_missing`.
- One behaviour per test, Arrange-Act-Assert, no comments that repeat the code.
- Use `pytest.mark.parametrize` for tables of inputs, like `test_invalid_create_never_calls_repository`.
- Reuse fixtures from `tests/conftest.py` (`client`, `repository_mock`, `todo`, `todo_values`, `model_factory`). Add a fixture to `conftest.py` only when two or more test modules need it.
- Only the packages in `backend/requirements.txt` are available: pytest, pytest-cov, httpx, FastAPI's `TestClient`, `unittest.mock`. Do not add pytest plugins.

## Patterns by layer

**Routers** (`app/features/*/router.py`, `app/api/*.py`): use the `client` fixture. It mounts only the todos router with `get_repository` overridden by an autospec mock. Assert both the HTTP response and how the repository was called:

```python
def test_get_returns_404_for_missing_task(client, repository_mock):
    repository_mock.get.return_value = None
    response = client.get("/api/todos/404")
    assert response.status_code == 404
    assert response.json() == {"detail": "Task not found."}
    repository_mock.get.assert_called_once_with(404)
```

For a router that is not in the `client` fixture (for example `app/api/health.py`), build a small `FastAPI()` app in the test, include that router and override `get_repository` the same way.

**Repository** (`repository.py`): pass `Mock(spec=Session)` and assert calls on it (`add`, `commit`, `refresh`, `delete`, `get`). Use `model_factory(todo_values)` to build records. For timestamps, patch the module's `datetime` or assert `updated_at` changed relative to a fixed value, never compare to the real clock.

**Schemas and validators**: call `Model.model_validate(...)` or `validate_patch_fields(...)` directly and assert on `pydantic.ValidationError` with `pytest.raises(..., match=...)`.

**Core** (`config.py`, `database.py`, `lifespan.py`, `factory.py`):
- `resolve_database_url`: use `monkeypatch.setenv`/`delenv` for every variable it reads, and patch `app.core.config.load_dotenv` so a developer's `.env` file cannot leak into the test.
- `lifespan`/`factory`: patch the collaborators where they are looked up (`app.core.lifespan.create_database_engine`, `...initialize`, `...create_session_factory`) and drive the context manager with `asyncio.run` or `TestClient(app)`. Assert the engine is disposed even when initialisation raises.
- `database.py`: `create_database_engine` does not connect until used, so engine properties can be checked without a server. Test `initialize` with a `Mock` engine and a patched `Base.metadata.create_all`.

**Dependencies** (`api/dependencies.py`): drive the generator by hand as in `tests/api/test_dependencies.py`: `next(gen)` for the happy path, `gen.throw(exc)` to test rollback, then assert `close()` was called.

## Mocks

- Prefer `create_autospec(Class, instance=True)` or `Mock(spec=...)` so a test fails when the mocked interface changes. `tests/mocks.py` has `make_repository_mock()`.
- Patch where a name is *used*, not where it is defined (`app.core.lifespan.initialize`, not `app.core.database.initialize`).

## Running

```bash
python3 tools/test-agent/run_tests.py backend backend/tests/features/todos/test_router.py --focus backend/app/features/todos/router.py
```

See the `run-unit-tests` skill for how to read the output.
