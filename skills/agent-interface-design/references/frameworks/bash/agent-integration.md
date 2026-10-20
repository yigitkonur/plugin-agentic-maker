# Bash: Agent-Readiness Check Script

> Read when: you need a short script that verifies a CLI is agent-ready: JSON output, not-found exit code, error structure and non-interactive behaviour.

The rules are in `../../cli/caller-integration.md` and `../../cli/caller-resilience.md`. A fuller suite is in `examples-tests.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#8. Integration Test Script -->
## Integration test script

Four checks: `version --json` carries `ok`; an unknown resource exits 3; a failing command's envelope has `error.code` and a non-null `error.retryable`; a confirming command with `--yes` and empty stdin does not hang (exit code other than 124 from `timeout 5`).

```bash
#!/bin/bash
# test-agent-integration.sh
# Validates CLI is agent-ready

CLI="mycli"
PASS=0
FAIL=0

pass() { PASS=$((PASS + 1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL + 1)); echo "  FAIL: $1"; }

test_json_output() {
    echo "Test: JSON output..."
    if $CLI version --json | jq -e '.ok' > /dev/null 2>&1; then
        pass "JSON output works"
    else
        fail "JSON output broken"
    fi
}

test_exit_codes() {
    echo "Test: Exit codes..."
    $CLI nonexistent-resource --json >/dev/null 2>&1
    if [ $? -eq 3 ]; then
        pass "Not-found returns 3"
    else
        fail "Wrong exit code"
    fi
}

test_error_structure() {
    echo "Test: Error structure..."
    if $CLI fail --json 2>/dev/null | jq -e '.error.code and .error.retryable != null' > /dev/null; then
        pass "Error structure correct"
    else
        fail "Error structure missing fields"
    fi
}

test_non_interactive() {
    echo "Test: Non-interactive mode..."
    echo "" | timeout 5 $CLI dangerous-cmd --yes --json > /dev/null 2>&1
    if [ $? -ne 124 ]; then
        pass "Non-interactive works"
    else
        fail "Command hangs"
    fi
}

# Run tests
test_json_output
test_exit_codes
test_error_structure
test_non_interactive

# Summary
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

> Reconciled: the source wrote each check as `[ ... ] && ((PASS++)) && echo ok || ((FAIL++)) && echo bad`. `((PASS++))` returns status 1 when the old value is 0, so the first pass fell through to the `||` branch and was also counted as a failure. This file uses `PASS=$((PASS + 1))` inside an `if`/`else`. The script has no `set -e`, so a failing check does not abort the run.
