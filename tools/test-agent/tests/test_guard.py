import io
import json

import pytest

import guard


def _patch(tmp_path, text):
    path = tmp_path / "tests.patch"
    path.write_text(text)
    return str(path)


NEW_TEST = """diff --git a/backend/tests/test_x.py b/backend/tests/test_x.py
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/backend/tests/test_x.py
@@ -0,0 +1 @@
+def test_x(): pass
"""


def test_verify_patch_accepts_test_files(tmp_path, capsys):
    assert guard.verify_patch(_patch(tmp_path, NEW_TEST)) == 0
    assert json.loads(capsys.readouterr().out) == {"files": ["backend/tests/test_x.py"]}


def test_verify_patch_rejects_source_files(tmp_path, capsys):
    text = NEW_TEST.replace("backend/tests/test_x.py", "backend/app/x.py")
    assert guard.verify_patch(_patch(tmp_path, text)) == 1
    assert "backend/app/x.py" in capsys.readouterr().err


@pytest.mark.parametrize("line", [
    "new file mode 100755",
    "new file mode 120000",
    "old mode 100644",
    "rename from backend/app/x.py",
])
def test_verify_patch_rejects_modes_symlinks_and_renames(tmp_path, line):
    text = NEW_TEST.replace("new file mode 100644", line)
    assert guard.verify_patch(_patch(tmp_path, text)) == 1


def test_verify_patch_rejects_unparseable_headers(tmp_path):
    text = NEW_TEST.replace("diff --git a/backend/tests/test_x.py b/backend/tests/test_x.py", "diff --git weird")
    assert guard.verify_patch(_patch(tmp_path, text)) == 1


def _run_hook(monkeypatch, capsys, tmp_path, file_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps({"tool_name": "Write", "tool_input": {"file_path": file_path}})))
    assert guard.hook() == 0
    out = capsys.readouterr().out
    return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out else "allow"


def test_hook_allows_test_files(monkeypatch, capsys, tmp_path):
    assert _run_hook(monkeypatch, capsys, tmp_path, str(tmp_path / "backend/tests/test_x.py")) == "allow"


@pytest.mark.parametrize("target", ["backend/app/x.py", "frontend/package.json", "backend/tests/../app/x.py"])
def test_hook_denies_other_files(monkeypatch, capsys, tmp_path, target):
    assert _run_hook(monkeypatch, capsys, tmp_path, str(tmp_path / target)) == "deny"


def test_hook_denies_paths_outside_project(monkeypatch, capsys, tmp_path):
    assert _run_hook(monkeypatch, capsys, tmp_path, "/tmp/backend/tests/test_x.py") == "deny"
