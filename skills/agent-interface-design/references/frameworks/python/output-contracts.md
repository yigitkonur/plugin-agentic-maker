# Python: Exit Codes, Field Selection, JSONL Emitters, Complete Example

> Read when: you are implementing the output contract of a Python CLI (exit constants, `--fields`, JSONL emitters, stdout/stderr split).

## Exit code constants

The table they implement is `../../cli/exit-codes.md`.

```python
# exitcodes.py
class ExitCode:
    SUCCESS = 0     # Operation completed successfully
    CRASH = 1       # Unexpected error, internal failure
    USAGE = 2       # Bad flags, invalid arguments
    NOT_FOUND = 3   # Resource does not exist
    AUTH = 4        # Authentication/authorization failed
    CONFLICT = 5    # Resource conflict (exists, version mismatch)
    VALIDATION = 6  # Input validation failed
    TRANSIENT = 7   # Retryable error (network, timeout, rate limit)
    PARTIAL = 8     # Partial success (some operations failed)

EXIT_BY_CLASS = {
    "usage": ExitCode.USAGE,
    "not_found": ExitCode.NOT_FOUND,
    "auth": ExitCode.AUTH,
    "conflict": ExitCode.CONFLICT,
    "validation": ExitCode.VALIDATION,
    "rate_limit": ExitCode.TRANSIENT,
    "timeout": ExitCode.TRANSIENT,
    "network": ExitCode.TRANSIENT,
    "dependency_failed": ExitCode.TRANSIENT,
    "partial_success": ExitCode.PARTIAL,
    "internal": ExitCode.CRASH,
}
```

## Field selection

```python
def filter_fields(data: dict, fields: list[str]) -> dict:
    if not fields:
        return data
    return {k: v for k, v in data.items() if k in fields}
```

## JSONL emitters

Contract: `../../cli/streams-and-jsonl.md`.

> Reconciled: the source printed progress to stdout and always exited 1 from `emit_error`. Progress goes to stderr; the terminal result goes to stdout; `emit_error` exits with the code for its class.

```python
import json
import sys
from datetime import datetime, timezone


def emit_progress(phase: str, percent: int, message: str = None):
    event = {
        "type": "progress",
        "phase": phase,
        "percent": percent,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    if message:
        event["message"] = message
    print(json.dumps(event), file=sys.stderr, flush=True)


def emit_completed(result: dict):
    event = {
        "type": "completed",
        "status": "succeeded",
        "result": result,
    }
    print(json.dumps(event), flush=True)


def emit_error(error_class: str, code: str, message: str):
    event = {
        "type": "error",
        "error": {
            "class": error_class,
            "code": code,
            "message": message,
        },
    }
    print(json.dumps(event), flush=True)
    sys.exit(EXIT_BY_CLASS.get(error_class, ExitCode.CRASH))
```

## Complete example

```python
import json
import sys


def main():
    # Progress to stderr
    print("Connecting to server...", file=sys.stderr)

    try:
        result = do_operation()
    except NetworkError as e:
        # Error JSON to stdout
        response = {
            "ok": False,
            "error": {
                "class": "network",
                "code": "CONNECTION_FAILED",
                "message": str(e),
            },
        }
        print(json.dumps(response))
        sys.exit(7)  # TRANSIENT

    # Success JSON to stdout
    response = {
        "ok": True,
        "result": result,
    }
    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
```
