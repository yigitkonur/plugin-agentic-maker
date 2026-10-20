# Bash: Parsing CLI JSON Responses with jq

> Read when: you need shell helpers that validate a CLI response, read the error class and retryability, extract fields and process a batch from a file.

Rules: `../../cli/caller-integration.md`. The wrapper and constants are in `examples-wrapper.md`.

<!-- src: audit-agentic-cli/references/examples.md#15.2 JSON Response Parsing with jq -->
## JSON response parsing with jq

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Parse CLI JSON Response
# ============================================================================

parse_response() {
    local response="$1"

    # Check if response is valid JSON
    if ! echo "$response" | jq -e . >/dev/null 2>&1; then
        echo "Error: Invalid JSON response" >&2
        return 1
    fi

    # Check ok field
    local ok
    ok=$(echo "$response" | jq -r '.ok')

    if [[ "$ok" != "true" ]]; then
        local error_class error_code error_message
        error_class=$(echo "$response" | jq -r '.error.class // "unknown"')
        error_code=$(echo "$response" | jq -r '.error.code // "UNKNOWN"')
        error_message=$(echo "$response" | jq -r '.error.message // "Unknown error"')

        echo "Error [$error_class/$error_code]: $error_message" >&2
        return 1
    fi

    # Return result
    echo "$response" | jq -r '.result'
}

# ============================================================================
# Extract Specific Fields
# ============================================================================

get_resource_id() {
    local response="$1"
    echo "$response" | jq -r '.result.id // empty'
}

get_resource_list() {
    local response="$1"
    echo "$response" | jq -r '.result.items[]?.id'
}

is_retryable_error() {
    local response="$1"
    local retryable
    retryable=$(echo "$response" | jq -r '.error.retryable // false')
    [[ "$retryable" == "true" ]]
}

# ============================================================================
# Batch Processing with jq
# ============================================================================

process_batch() {
    local input_file="$1"
    local output_file="${2:-/dev/stdout}"

    # Process each line as JSON
    while IFS= read -r line; do
        local id
        id=$(echo "$line" | jq -r '.id')

        local result
        if result=$(mycli get "$id" --json 2>/dev/null); then
            echo "$result" | jq -c '{id: .result.id, status: "success", data: .result}'
        else
            echo "$result" | jq -c --arg id "$id" '{id: $id, status: "error", error: .error}'
        fi
    done < "$input_file" > "$output_file"
}

# ============================================================================
# Usage Example
# ============================================================================

main() {
    export MYCLI_JSON=true

    # Create and capture response (the envelope is on stdout)
    local response
    if response=$(mycli create "my-resource" --json 2>/dev/null); then
        local resource_id
        resource_id=$(get_resource_id "$response")
        echo "Created resource: $resource_id"
    else
        if is_retryable_error "$response"; then
            echo "Transient error - retrying..."
            retry_with_backoff 3 2 30 mycli create "my-resource" --json
        else
            echo "Non-retryable error" >&2
            exit 1
        fi
    fi
}

[[ "${BASH_SOURCE[0]}" == "${0}" ]] && main "$@"
```

> Reconciled: the source captured `2>&1`, mixing stderr text into the JSON it then parsed; this file captures stdout only. It reads list items from `.result.items` (was `.result.resources`) and passes `$id` to jq with `--arg` instead of splicing it into the program text.
