# Python: Calling a CLI from an Agent

> Read when: you are writing the Python wrapper that runs a CLI with `subprocess`: JSON invocation, exit-code routing, retry, recovery hints, batches, and an AutoGen tool registration.

The rules are in `../../cli/caller-integration.md`.

## Basic invocation

```python
import subprocess
import json
from typing import TypedDict, Optional

class CLIResult(TypedDict):
    ok: bool
    result: Optional[dict]
    error: Optional[dict]

def invoke_cli(cmd: list[str], timeout: int = 30) -> CLIResult:
    """Invoke CLI with JSON output, proper error handling."""
    try:
        result = subprocess.run(
            cmd + ["--json"],
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Parse JSON from stdout (the envelope, success or failure)
        if result.stdout.strip():
            return json.loads(result.stdout)

        # No output = check exit code
        if result.returncode == 0:
            return {"ok": True, "result": None, "error": None}

        # Error without JSON body
        return {
            "ok": False,
            "result": None,
            "error": {
                "class": "internal",
                "code": f"exit_{result.returncode}",
                "message": result.stderr.strip() or "Unknown error"
            }
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "result": None, "error": {"class": "timeout", "code": "timeout", "retryable": True}}
    except json.JSONDecodeError as e:
        return {"ok": False, "result": None, "error": {"class": "internal", "code": "invalid_json", "message": str(e)}}
```

## Exit-code routing

```python
EXIT_CODE_ACTIONS = {
    0: "success",      # Proceed with result
    1: "crash",        # Log error, escalate to human
    2: "usage",        # Fix command syntax
    3: "not_found",    # Resource doesn't exist
    4: "auth",         # Re-authenticate
    5: "conflict",     # Resolve conflict, retry
    6: "validation",   # Fix input data
    7: "transient",    # Retry with backoff
    8: "partial",      # Read per-item results
    130: "interrupted",  # SIGINT stop: do not retry
    143: "terminated",   # SIGTERM stop: do not retry
}

def route_exit_code(code: int) -> str:
    """Map exit code to appropriate action."""
    return EXIT_CODE_ACTIONS.get(code, "unknown")
```

## Retry with exponential backoff

```python
import time
import random

def invoke_with_retry(
    cmd: list[str],
    max_retries: int = 3,
    base_delay: float = 1.0
) -> CLIResult:
    """Invoke CLI with intelligent retry for transient errors."""

    for attempt in range(max_retries + 1):
        result = invoke_cli(cmd)

        # Success - return immediately
        if result["ok"]:
            return result

        error = result.get("error", {})

        # Not retryable - fail fast
        if not error.get("retryable", False):
            return result

        # Last attempt - return error
        if attempt == max_retries:
            return result

        # Calculate backoff with jitter
        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)

        # Honor Retry-After hint if present
        if "retry_after" in error:
            delay = max(delay, error["retry_after"])

        time.sleep(delay)

    return result
```

## Error recovery hints

```python
def handle_cli_error(result: CLIResult, context: dict) -> str:
    """Generate recovery action from CLI error."""

    error = result.get("error", {})
    error_class = error.get("class", "unknown")

    RECOVERY_ACTIONS = {
        "auth": "Re-run auth: mycli auth login",
        "not_found": f"Resource {context.get('resource')} does not exist. Create it first.",
        "conflict": f"Conflict detected. Use --force or resolve: {error.get('suggestion', '')}",
        "validation": f"Invalid input: {error.get('message')}. Fix: {error.get('suggestion', '')}",
        "rate_limit": f"Rate limited. Wait {error.get('retry_after', 60)}s before retry.",
        # exit-7 group: the retry loop handles these
        "timeout": "Temporary failure. Retry automatically handled.",
        "network": "Temporary failure. Retry automatically handled.",
        "dependency_failed": "Temporary failure. Retry automatically handled.",
    }

    return RECOVERY_ACTIONS.get(error_class, f"Unknown error: {error.get('message')}")
```

> Note: the dict is keyed by class `auth` and lists the exit-7 classes (`timeout`, `network`, `dependency_failed`) individually; `EXIT_CODE_ACTIONS` includes `8: "partial"`.

## Batch with partial failure

```python
def batch_invoke(
    items: list[dict],
    cmd_template: list[str],
    batch_size: int = 10
) -> dict:
    """Process items in batches, handle partial failures."""

    results = {"succeeded": [], "failed": [], "total": len(items)}

    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        for item in batch:
            cmd = [c.format(**item) for c in cmd_template]
            result = invoke_with_retry(cmd)

            if result["ok"]:
                results["succeeded"].append({
                    "item": item,
                    "result": result["result"]
                })
            else:
                results["failed"].append({
                    "item": item,
                    "error": result["error"]
                })

    return results
```

<!-- src: audit-agentic-cli/references/agent-integration.md#AutoGen Integration -->
## AutoGen integration

Illustrative; framework APIs change, verify against the current AutoGen docs.

```python
from autogen import AssistantAgent, UserProxyAgent, register_function
import subprocess
import json

def invoke_cli(command: str, timeout: int = 30, dry_run: bool = False) -> dict:
    """
    Execute CLI command with JSON output.

    Args:
        command: Full CLI command string
        timeout: Command timeout in seconds
        dry_run: If True, adds --dry-run flag

    Returns:
        Structured JSON result with ok, result, error fields
    """
    cmd = command.split() + ['--json', '--quiet']
    if dry_run:
        cmd.append('--dry-run')

    result = None
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.stdout.strip():
            return json.loads(result.stdout)
        return {'ok': result.returncode == 0}
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': {'code': 'timeout', 'retryable': True}}
    except json.JSONDecodeError:
        return {'ok': False, 'error': {'code': 'invalid_json', 'message': result.stdout}}

# Register with AutoGen
assistant = AssistantAgent("cli_assistant", llm_config=llm_config)
user_proxy = UserProxyAgent("user_proxy", code_execution_config=False)

register_function(
    invoke_cli,
    caller=assistant,
    executor=user_proxy,
    description="Execute CLI commands with structured JSON output"
)
```
