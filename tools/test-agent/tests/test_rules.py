import pytest

import rules


@pytest.mark.parametrize("path, area, kind, testable", [
    ("backend/app/features/todos/router.py", "backend", "source", True),
    ("backend/app/core/config.py", "backend", "source", True),
    ("backend/app/main.py", "backend", "source", False),
    ("backend/app/features/todos/models.py", "backend", "source", False),
    ("backend/app/__init__.py", "backend", "source", False),
    ("backend/tests/features/todos/test_router.py", "backend", "test", False),
    ("frontend/src/lib/http.ts", "frontend", "source", True),
    ("frontend/src/features/todos/TodosPage.tsx", "frontend", "source", True),
    ("frontend/src/features/todos/TodosPage.test.tsx", "frontend", "test", False),
    ("frontend/src/design-system/components/Button/Button.tsx", "frontend", "source", False),
    ("frontend/src/features/todos/types.ts", "frontend", "source", False),
    ("frontend/src/features/todos/index.ts", "frontend", "source", False),
    ("frontend/src/main.tsx", "frontend", "source", False),
    ("README.md", None, "other", False),
    ("frontend/package.json", None, "other", False),
    ("frontend/src/styles.css", None, "other", False),
    (".github/workflows/ci.yml", None, "other", False),
])
def test_classify(path, area, kind, testable):
    c = rules.classify(path)
    assert (c.area, c.kind, c.testable) == (area, kind, testable)


@pytest.mark.parametrize("source, expected", [
    ("backend/app/features/todos/router.py", "backend/tests/features/todos/test_router.py"),
    ("backend/app/factory.py", "backend/tests/test_factory.py"),
    ("frontend/src/lib/http.ts", "frontend/src/lib/http.test.ts"),
    ("frontend/src/App.tsx", "frontend/src/App.test.tsx"),
    ("README.md", None),
])
def test_default_test_path(source, expected):
    assert rules.default_test_path(source) == expected


@pytest.mark.parametrize("path", [
    "backend/tests/test_factory.py",
    "backend/tests/core/test_config.py",
    "backend/tests/core/__init__.py",
    "backend/tests/conftest.py",
    "backend/tests/mocks.py",
    "frontend/src/lib/http.test.ts",
    "frontend/src/features/todos/hooks/useTodosQuery.test.tsx",
    "frontend/src/test/queryWrapper.tsx",
    "./backend/tests/test_x.py",
])
def test_test_files_are_writable(path):
    assert rules.is_writable(path)


@pytest.mark.parametrize("path", [
    "backend/app/factory.py",
    "backend/tests/../app/factory.py",
    "backend/tests/data.json",
    "backend/requirements.txt",
    "frontend/src/lib/http.ts",
    "frontend/src/lib/http.test.ts.bak",
    "frontend/package.json",
    "frontend/vite.config.ts",
    "frontend/src/test/nested/evil.ts",
    ".github/workflows/test-agent.yml",
    ".claude/agents/test-engineer.md",
    "tools/test-agent/guard.py",
    "/etc/passwd",
    "../outside/backend/tests/test_x.py",
    "C:/backend/tests/test_x.py",
])
def test_everything_else_is_not_writable(path):
    assert not rules.is_writable(path)


def test_normalize_resolves_dot_segments():
    assert rules.normalize("backend/./tests/core/../test_x.py") == "backend/tests/test_x.py"
    assert rules.normalize("..") is None
