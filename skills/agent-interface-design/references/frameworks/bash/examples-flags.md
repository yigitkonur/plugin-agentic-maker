# Bash: Standard Flag Parsing

> Read when: you need a Bash script that parses the standard flags (`--json`, `-q`, `-y`, `-f`, `--dry-run`, `--timeout`) and exits 2 on bad usage.

Rules: `../../cli/discovery-and-help.md`.

<!-- src: audit-agentic-cli/references/examples.md#15.3 Flag Parsing in Bash -->
## Flag parsing in Bash

```bash
#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Standard Flag Parsing (matching all languages)
# ============================================================================

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] COMMAND [ARGS]

Options:
    --json              Output as JSON
    -q, --quiet         Minimal output
    -y, --yes           Auto-confirm prompts
    -f, --force         Force operation
    --dry-run           Preview without executing
    --timeout SECONDS   Operation timeout (default: 30)
    -h, --help          Show this help

Commands:
    create NAME         Create a resource
    list                List resources
    get ID              Get a resource
    delete ID           Delete a resource

Examples:
    $(basename "$0") create my-resource --json
    $(basename "$0") delete res_123 --yes
    $(basename "$0") list --quiet
EOF
    exit "${1:-0}"
}

# Parse flags
JSON_OUTPUT=false
QUIET=false
YES=false
FORCE=false
DRY_RUN=false
TIMEOUT=30

while [[ $# -gt 0 ]]; do
    case "$1" in
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        -y|--yes)
            YES=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --timeout=*)
            TIMEOUT="${1#*=}"
            shift
            ;;
        -h|--help)
            usage 0
            ;;
        --)
            shift
            break
            ;;
        -*)
            echo "Unknown option: $1" >&2
            usage 2
            ;;
        *)
            break
            ;;
    esac
done

# Remaining args are command and arguments
COMMAND="${1:-}"
shift || true

case "$COMMAND" in
    create)
        NAME="${1:-}"
        [[ -z "$NAME" ]] && { echo "Error: NAME required" >&2; exit 2; }
        # ... create logic
        ;;
    list)
        # ... list logic
        ;;
    get|delete)
        ID="${1:-}"
        [[ -z "$ID" ]] && { echo "Error: ID required" >&2; exit 2; }
        # ... get/delete logic
        ;;
    "")
        echo "Error: COMMAND required" >&2
        usage 2
        ;;
    *)
        echo "Unknown command: $COMMAND" >&2
        usage 2
        ;;
esac
```
