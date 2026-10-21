"""Path rules shared by the planner, the write guard hook and the diff guard.

Keeping them in one module means the files the agent is asked to test, the
files it may write, and the files the workflow will commit can never drift
apart.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import PurePosixPath

BACKEND = "backend"
FRONTEND = "frontend"

# Source files that hold testable behaviour.
_SOURCE_PATTERNS = {
    BACKEND: ["backend/app/**.py"],
    FRONTEND: ["frontend/src/**.ts", "frontend/src/**.tsx"],
}

# Source files with no unit-testable logic of their own. These mirror the
# coverage `omit`/`exclude` settings of each project, plus presentational
# files (stories, styles) that are covered by Storybook rather than unit tests.
_NON_TESTABLE_PATTERNS = {
    BACKEND: [
        "backend/app/**/__init__.py",
        "backend/app/__init__.py",
        "backend/app/main.py",
        "backend/app/**/models.py",
        "backend/app/**/types.py",
        "backend/app/**/constants.py",
    ],
    FRONTEND: [
        "frontend/src/main.tsx",
        "frontend/src/test/**",
        "frontend/src/**/*.stories.tsx",
        "frontend/src/**/*.styles.ts",
        "frontend/src/**/*.variants.ts",
        "frontend/src/**/types.ts",
        "frontend/src/**/*.types.ts",
        "frontend/src/**/*.d.ts",
        "frontend/src/**/index.ts",
        "frontend/src/**/constants.ts",
        "frontend/src/**/*.constants.ts",
        # The design system is excluded from coverage and documented via Storybook.
        "frontend/src/design-system/**",
        "frontend/src/lib/queryClient.ts",
        "frontend/src/features/todos/api/queryKeys.ts",
    ],
}

# Files the agent is allowed to create or modify. Anything else is rejected
# both while the agent runs (PreToolUse hook) and before the commit.
_WRITABLE_PATTERNS = [
    "backend/tests/**/test_*.py",
    "backend/tests/test_*.py",
    "backend/tests/**/__init__.py",
    "backend/tests/__init__.py",
    "backend/tests/**/conftest.py",
    "backend/tests/conftest.py",
    "backend/tests/mocks.py",
    "frontend/src/**/*.test.ts",
    "frontend/src/**/*.test.tsx",
    "frontend/src/test/*.ts",
    "frontend/src/test/*.tsx",
]

_TEST_PATTERNS = {
    BACKEND: ["backend/tests/**"],
    FRONTEND: ["frontend/src/**/*.test.ts", "frontend/src/**/*.test.tsx", "frontend/src/test/**"],
}


def _glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Translate a glob where `**` spans directories and `*` stays in one segment."""
    out = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


_COMPILED: dict[str, re.Pattern[str]] = {}


def matches(path: str, patterns: list[str]) -> bool:
    for pattern in patterns:
        regex = _COMPILED.setdefault(pattern, _glob_to_regex(pattern))
        if regex.match(path):
            return True
    return False


def normalize(path: str) -> str | None:
    """Return a clean repo-relative POSIX path, or None if it escapes the repo."""
    path = path.replace("\\", "/")
    if path.startswith("/") or re.match(r"^[A-Za-z]:", path):
        return None
    parts: list[str] = []
    for part in PurePosixPath(path).parts:
        if part in ("", "."):
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
            continue
        parts.append(part)
    return "/".join(parts) if parts else None


@dataclass(frozen=True)
class Classification:
    area: str | None  # "backend", "frontend" or None
    kind: str  # "source", "test" or "other"
    testable: bool
    reason: str


def classify(path: str) -> Classification:
    for area in (BACKEND, FRONTEND):
        if matches(path, _TEST_PATTERNS[area]):
            return Classification(area, "test", False, "test file")
    for area in (BACKEND, FRONTEND):
        if matches(path, _SOURCE_PATTERNS[area]):
            if matches(path, _NON_TESTABLE_PATTERNS[area]):
                return Classification(area, "source", False, "declarative or presentational file, excluded from coverage")
            return Classification(area, "source", True, "application source")
    return Classification(None, "other", False, "not application source (docs, config, styles or tooling)")


def default_test_path(path: str) -> str | None:
    """Conventional location of the unit test for a source file."""
    p = PurePosixPath(path)
    if path.startswith("backend/app/"):
        rel = p.relative_to("backend/app")
        return str(PurePosixPath("backend/tests") / rel.parent / f"test_{rel.name}")
    if path.startswith("frontend/src/") and p.suffix in (".ts", ".tsx"):
        return str(p.with_name(f"{p.stem}.test{p.suffix}"))
    return None


def is_writable(path: str) -> bool:
    clean = normalize(path)
    return clean is not None and matches(clean, _WRITABLE_PATTERNS)

