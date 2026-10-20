# Python: Testing JSON Output

> Read when: you need pytest tests that run the CLI and check exit code and envelope fields.

<!-- src: audit-agentic-cli/references/examples.md#16.2 Unit Testing JSON Output (Python) -->
## Unit testing JSON output

```python
import json
import subprocess
import pytest
from typing import Any

def run_cli(*args: str) -> tuple[int, dict[str, Any]]:
    """Run CLI and return (exit_code, parsed_json). The envelope is on stdout."""
    result = subprocess.run(
        ["mycli", *args, "--json"],
        capture_output=True,
        text=True
    )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        data = {"raw": result.stdout, "stderr": result.stderr}

    return result.returncode, data

class TestCLIOutput:
    def test_create_success(self):
        exit_code, data = run_cli("create", "test-resource")

        assert exit_code == 0
        assert data["ok"] is True
        assert "result" in data
        assert data["result"]["created"] is True

    def test_get_not_found(self):
        exit_code, data = run_cli("get", "nonexistent")

        assert exit_code == 3  # EXIT_NOT_FOUND
        assert data["ok"] is False
        assert data["error"]["class"] == "not_found"
        assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert data["error"]["retryable"] is False

    def test_delete_requires_confirmation(self):
        exit_code, data = run_cli("delete", "res_123")

        assert exit_code == 2  # EXIT_USAGE
        assert data["ok"] is False
        assert data["error"]["class"] == "usage"

    def test_delete_with_yes_flag(self):
        exit_code, data = run_cli("delete", "res_123", "-y")

        assert exit_code == 0
        assert data["ok"] is True

    def test_dry_run_returns_preview(self):
        exit_code, data = run_cli("create", "test", "--dry-run")

        assert exit_code == 0
        assert data["ok"] is True
        assert data["result"]["dry_run"] is True

    @pytest.mark.parametrize("flag,short", [
        ("--quiet", "-q"),
        ("--yes", "-y"),
        ("--force", "-f"),
    ])
    def test_short_flags_work(self, flag, short):
        """Ensure short flag aliases work identically."""
        _, data1 = run_cli("list", flag)
        _, data2 = run_cli("list", short)

        # Results should be structurally identical
        assert data1.get("ok") == data2.get("ok")
```

> Reconciled: the source read `stdout or stderr`; the envelope is always on stdout, so the helper reads stdout only.
