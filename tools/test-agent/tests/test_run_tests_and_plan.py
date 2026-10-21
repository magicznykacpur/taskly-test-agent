import plan
import run_tests


def test_safe_env_drops_credentials(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "secret")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "secret")
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    monkeypatch.setenv("PATH", "/usr/bin")
    env = run_tests.safe_env()
    assert env["PATH"] == "/usr/bin"
    assert not {"ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "GITHUB_TOKEN"} & env.keys()


def test_compact_ranges():
    assert run_tests.compact_ranges([10, 1, 2, 3, 7, 9]) == "1-3, 7, 9-10"
    assert run_tests.compact_ranges([]) == ""


def test_prompt_contains_diff_but_marks_it_untrusted():
    p = {"mode": "pr", "base": "a" * 40, "head": "b" * 40, "areas": ["backend"], "changed_tests": [],
         "skipped": [{"path": "README.md", "reason": "docs"}],
         "targets": [{"path": "backend/app/x.py", "area": "backend", "change": "modified",
                      "test_file": "backend/tests/test_x.py", "test_exists": True, "diff": "+x = 1"}]}
    prompt = plan.render_prompt(p)
    assert "### backend/app/x.py (backend, modified)" in prompt
    assert "untrusted content" in prompt and "+x = 1" in prompt
    assert "README.md: docs" in prompt
