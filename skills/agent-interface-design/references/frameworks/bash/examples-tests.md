# Bash: CLI Integration Test Suite

> Read when: you need a Bash test script that runs a CLI and asserts exit codes and JSON fields with correct pass/fail counting.

Rules: `../../cli/exit-codes.md`, `../../cli/envelope-and-errors.md`. A smaller agent-readiness check is in `agent-integration.md`.

<!-- src: audit-agentic-cli/references/examples.md#16.5 Integration Test Script (Bash) -->
## Integration test script

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# CLI Integration Test Suite
# ============================================================================

TESTS_PASSED=0
TESTS_FAILED=0
CLI_BIN="${CLI_BIN:-./mycli}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

assert_exit_code() {
    local expected="$1"
    local actual="$2"
    local test_name="$3"

    if [[ "$actual" -eq "$expected" ]]; then
        echo -e "${GREEN}✓${NC} $test_name (exit=$actual)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name: expected exit=$expected, got exit=$actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_json_field() {
    local json="$1"
    local field="$2"
    local expected="$3"
    local test_name="$4"

    local actual
    actual=$(echo "$json" | jq -r "$field")

    if [[ "$actual" == "$expected" ]]; then
        echo -e "${GREEN}✓${NC} $test_name ($field=$actual)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $test_name: $field expected '$expected', got '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# ============================================================================
# Test: Create Success
# ============================================================================
test_create_success() {
    local output exit_code
    output=$($CLI_BIN create test-resource --json 2>/dev/null) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 0 "$exit_code" "create: exit code"
    assert_json_field "$output" '.ok' 'true' "create: ok=true"
    assert_json_field "$output" '.result.created' 'true' "create: result.created"
}

# ============================================================================
# Test: Get Not Found
# ============================================================================
test_get_not_found() {
    local output exit_code
    output=$($CLI_BIN get nonexistent --json 2>/dev/null) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 3 "$exit_code" "get not found: exit code"
    assert_json_field "$output" '.ok' 'false' "get not found: ok=false"
    assert_json_field "$output" '.error.class' 'not_found' "get not found: error.class"
    assert_json_field "$output" '.error.retryable' 'false' "get not found: not retryable"
}

# ============================================================================
# Test: Delete Requires Confirmation
# ============================================================================
test_delete_needs_confirm() {
    local output exit_code
    output=$($CLI_BIN delete res_123 --json 2>/dev/null </dev/null) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 2 "$exit_code" "delete no confirm: exit code"
    assert_json_field "$output" '.error.class' 'usage' "delete no confirm: error.class"
}

# ============================================================================
# Test: Delete with --yes
# ============================================================================
test_delete_with_yes() {
    local output exit_code
    output=$($CLI_BIN delete res_123 --yes --json 2>/dev/null) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 0 "$exit_code" "delete --yes: exit code"
    assert_json_field "$output" '.ok' 'true' "delete --yes: ok=true"
}

# ============================================================================
# Test: Dry Run
# ============================================================================
test_dry_run() {
    local output exit_code
    output=$($CLI_BIN create test --dry-run --json 2>/dev/null) || exit_code=$?
    exit_code=${exit_code:-0}

    assert_exit_code 0 "$exit_code" "dry-run: exit code"
    assert_json_field "$output" '.result.dry_run' 'true' "dry-run: result.dry_run"
}

# ============================================================================
# Test: Short Flags
# ============================================================================
test_short_flags() {
    local flags=("-q:--quiet" "-y:--yes" "-f:--force")

    for pair in "${flags[@]}"; do
        local short="${pair%%:*}"
        local long="${pair##*:}"

        local out1 out2
        out1=$($CLI_BIN list "$long" --json 2>/dev/null) || true
        out2=$($CLI_BIN list "$short" --json 2>/dev/null) || true

        local ok1 ok2
        ok1=$(echo "$out1" | jq -r '.ok')
        ok2=$(echo "$out2" | jq -r '.ok')

        if [[ "$ok1" == "$ok2" ]]; then
            echo -e "${GREEN}✓${NC} flag alias: $short == $long"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} flag alias: $short != $long"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    done
}

# ============================================================================
# Run All Tests
# ============================================================================
main() {
    echo "Running CLI Integration Tests..."
    echo "================================"

    test_create_success
    test_get_not_found
    test_delete_needs_confirm
    test_delete_with_yes
    test_dry_run
    test_short_flags

    echo "================================"
    echo -e "Results: ${GREEN}$TESTS_PASSED passed${NC}, ${RED}$TESTS_FAILED failed${NC}"

    if [[ "$TESTS_FAILED" -gt 0 ]]; then
        exit 1
    fi
}

main "$@"
```

> Reconciled: the source counted with `((TESTS_PASSED++))`, which evaluates to the old value; when that is 0 (the first pass) the arithmetic command returns status 1 and `set -e` aborts the script, so the first pass was lost or fatal. This file uses `TESTS_PASSED=$((TESTS_PASSED + 1))` (and the same for failures). Commands read stdout only (`2>/dev/null`), because the envelope is on stdout; the confirmation test redirects stdin from `/dev/null` to prove the no-TTY exit 2.
