# Bash: Wrapper with Retry and jq Output Helpers

> Read when: you need a Bash wrapper around a CLI with standard exit-code constants, JSON helpers, retry on exit 7 and a non-interactive-safe delete.

Rules: `../../cli/caller-integration.md`, `../../cli/exit-codes.md`. Response parsing is in `examples-parsing.md`; flag parsing in `examples-flags.md`; tests in `examples-tests.md`.

<!-- src: audit-agentic-cli/references/examples.md#15. Shell/Bash Wrapper Scripts | audit-agentic-cli/references/examples.md#15.1 Basic Wrapper with jq Parsing -->
## Basic wrapper with jq parsing

Production-ready shell patterns for agent automation.

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Standard Exit Codes (matching all languages)
# ============================================================================
readonly EXIT_SUCCESS=0
readonly EXIT_CRASH=1
readonly EXIT_USAGE=2
readonly EXIT_NOT_FOUND=3
readonly EXIT_AUTH=4
readonly EXIT_CONFLICT=5
readonly EXIT_VALIDATION=6
readonly EXIT_TRANSIENT=7
readonly EXIT_PARTIAL=8

# ============================================================================
# Configuration
# ============================================================================
MYCLI_JSON="${MYCLI_JSON:-false}"
MYCLI_QUIET="${MYCLI_QUIET:-false}"
MYCLI_YES="${MYCLI_YES:-false}"
MYCLI_DRY_RUN="${MYCLI_DRY_RUN:-false}"
MYCLI_FORCE="${MYCLI_FORCE:-false}"
MYCLI_TIMEOUT="${MYCLI_TIMEOUT:-30}"

# ============================================================================
# JSON Output Helpers
# ============================================================================

json_success() {
    local result="$1"
    if [[ "$MYCLI_JSON" == "true" ]]; then
        jq -n --argjson result "$result" '{ok: true, result: $result}'
    else
        echo "$result" | jq -r '.'
    fi
}

json_error() {
    local class="$1"
    local code="$2"
    local message="$3"
    local retryable="${4:-false}"
    local exit_code="${5:-1}"

    if [[ "$MYCLI_JSON" == "true" ]]; then
        # The envelope goes to stdout; stderr is for human text only.
        jq -n \
            --arg class "$class" \
            --arg code "$code" \
            --arg message "$message" \
            --argjson retryable "$retryable" \
            '{ok: false, error: {class: $class, code: $code, message: $message, retryable: $retryable}}'
    else
        echo "Error: $message" >&2
    fi
    exit "$exit_code"
}

# ============================================================================
# Retry Logic with Exponential Backoff
# ============================================================================

retry_with_backoff() {
    local max_attempts="${1:-3}"
    local base_delay="${2:-1}"
    local max_delay="${3:-60}"
    shift 3

    local attempt=1
    local delay="$base_delay"

    while (( attempt <= max_attempts )); do
        local exit_code=0
        "$@" || exit_code=$?

        if (( exit_code == 0 )); then
            return 0
        fi

        # Only retry transient errors (exit code 7)
        if (( exit_code != EXIT_TRANSIENT )); then
            return "$exit_code"
        fi

        if (( attempt < max_attempts )); then
            echo "Attempt $attempt failed. Retrying in ${delay}s..." >&2
            sleep "$delay"
            delay=$(( delay * 2 ))
            (( delay > max_delay )) && delay="$max_delay"
        fi

        attempt=$(( attempt + 1 ))
    done

    return "$EXIT_TRANSIENT"
}

# ============================================================================
# CLI Wrapper Function
# ============================================================================

mycli_wrapper() {
    local cmd="$1"
    shift

    # Build command arguments
    local args=()
    [[ "$MYCLI_JSON" == "true" ]] && args+=(--json)
    [[ "$MYCLI_QUIET" == "true" ]] && args+=(-q)
    [[ "$MYCLI_YES" == "true" ]] && args+=(-y)
    [[ "$MYCLI_DRY_RUN" == "true" ]] && args+=(--dry-run)
    [[ "$MYCLI_FORCE" == "true" ]] && args+=(-f)
    [[ -n "$MYCLI_TIMEOUT" ]] && args+=(--timeout "$MYCLI_TIMEOUT")

    # Execute with timeout
    timeout "$MYCLI_TIMEOUT" mycli "$cmd" "${args[@]}" "$@"
}

# ============================================================================
# Example: Create Resource with Retry
# ============================================================================

create_resource() {
    local name="$1"
    local type="${2:-default}"

    retry_with_backoff 3 2 30 mycli_wrapper create "$name" --resource-type "$type"
}

# ============================================================================
# Example: Safe Delete with Confirmation
# ============================================================================

delete_resource() {
    local id="$1"

    if [[ "$MYCLI_YES" != "true" && "$MYCLI_FORCE" != "true" ]]; then
        # No TTY and no --yes/--force: fail with exit 2 naming the flag; never hang
        if [[ ! -t 0 ]]; then
            echo "Error: confirmation required: pass --yes or --force" >&2
            exit "$EXIT_USAGE"
        fi
        read -r -p "Delete resource '$id'? [y/N] " response
        if [[ ! "$response" =~ ^[Yy]$ ]]; then
            echo "Aborted." >&2
            exit "$EXIT_USAGE"
        fi
    fi

    mycli_wrapper delete "$id"
}
```

> Reconciled: the source labelled 1 `EXIT_ERROR` and stopped at 7; this file uses `EXIT_CRASH` and adds `EXIT_PARTIAL=8`. `json_error` wrote the envelope to stderr; it now writes to stdout. The source's `retry_with_backoff` read `$?` after the `if`, which is always 0, so it never retried and reported failures as success; it now captures the status of the command itself. `delete_resource` now exits 2 naming the flag when there is no TTY instead of blocking on `read`.
