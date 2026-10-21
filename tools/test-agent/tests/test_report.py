import json

import report


def _write(d, name, data):
    (d / name).write_text(json.dumps(data) if not isinstance(data, str) else data)


PLAN = {
    "areas": ["backend"],
    "targets": [{"path": "backend/app/x.py", "area": "backend"}],
    "skipped": [{"path": "README.md", "reason": "docs"}],
    "changed_tests": [],
}
AGENT = {
    "structured_output": {
        "summary": "Added tests. Ping @someone <script>x</script>",
        "decisions": [{"source_file": "backend/app/x.py", "action": "created", "test_file": "backend/tests/test_x.py",
                       "tests_added": 2, "reason": "New | module"}],
        "skills_used": ["pytest-unit-tests"],
        "findings": [],
    },
    "num_turns": 5, "duration_ms": 30000, "total_cost_usd": 0.12,
}
RESULT = {"ok": True, "passed": 3, "failed": 0, "coverage": {"total_pct": 90.0, "files": {"backend/app/x.py": {"lines_pct": 100.0}}}}


def test_success_report_contains_decisions_verification_and_safe_text(tmp_path):
    _write(tmp_path, "plan.json", PLAN)
    _write(tmp_path, "agent-result.json", AGENT)
    _write(tmp_path, "guard.txt", "ok")
    _write(tmp_path, "before-backend.json", {**RESULT, "coverage": {"total_pct": 50.0, "files": {}}})
    _write(tmp_path, "after-backend.json", RESULT)
    body, status = report.render(tmp_path, "abc123", "https://run", None)
    assert status == "success"
    assert body.startswith(report.MARKER)
    assert "50.0% → 90.0%" in body
    assert "| `backend/app/x.py` | n/a | 100.0% |" in body
    assert "@​someone" in body and "<script>" not in body
    assert "New \\| module" in body
    assert "abc123" in body and "$0.12" in body


def test_failing_verification_is_reported_as_failure(tmp_path):
    _write(tmp_path, "plan.json", PLAN)
    _write(tmp_path, "guard.txt", "ok")
    _write(tmp_path, "after-backend.json", {"ok": False, "passed": 1, "failed": 1,
                                            "failures": [{"test": "t::x", "message": "assert 1 == 2"}]})
    body, status = report.render(tmp_path, None, None, "Not committed.")
    assert status == "failure"
    assert "assert 1 == 2" in body and "Not committed." in body


def test_guard_violation_is_a_failure(tmp_path):
    _write(tmp_path, "plan.json", PLAN)
    _write(tmp_path, "guard.txt", "Changes outside allowed test paths:\n  backend/app/x.py")
    _write(tmp_path, "after-backend.json", RESULT)
    body, status = report.render(tmp_path, None, None, None)
    assert status == "failure"
    assert "backend/app/x.py" in body


def test_nothing_to_test_is_skipped(tmp_path):
    _write(tmp_path, "plan.json", {"areas": [], "targets": [], "skipped": [{"path": "README.md", "reason": "docs"}], "changed_tests": []})
    _write(tmp_path, "guard.txt", "ok")
    _, status = report.render(tmp_path, None, None, None)
    assert status == "skipped"
