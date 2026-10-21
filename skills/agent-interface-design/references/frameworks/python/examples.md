# Python: JSONL Streaming, Dry-Run and Credential Resolution

> Read when: you need Python code for typed JSONL events, a dry-run planner, or credential resolution that follows the standard precedence.

Rules: `../../cli/streams-and-jsonl.md`, `../../cli/checks.md`, `../../cli/auth-and-secrets.md`. Tests: `examples-tests.md`.

<!-- src: audit-agentic-cli/references/examples.md#2. JSONL Streaming (Python) -->
## JSONL streaming

```python
import json
import sys
from datetime import datetime, timezone
from typing import Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class StreamEvent:
    type: str
    timestamp: str = None
    phase: Optional[str] = None
    percent: Optional[int] = None
    message: Optional[str] = None
    data: Optional[Any] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

def emit_event(event: StreamEvent):
    """Emit one JSONL event in stream mode: progress/log to stderr, results to stdout."""
    d = {k: v for k, v in asdict(event).items() if v is not None}
    line = json.dumps(d)

    if event.type in ('progress', 'log'):
        print(line, file=sys.stderr, flush=True)
    else:
        print(line, flush=True)

# Usage
emit_event(StreamEvent(type='progress', phase='downloading', percent=25))
emit_event(StreamEvent(type='progress', phase='building', percent=75))
emit_event(StreamEvent(type='completed', data={'id': 'build_123'}))
```

<!-- src: audit-agentic-cli/references/examples.md#5. Dry-Run Implementation (Python) -->
## Dry-run implementation

```python
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class ChangeAction(Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    NOOP = "noop"

@dataclass
class PlannedChange:
    action: ChangeAction
    resource_type: str
    resource_id: str
    before: Optional[Dict[str, Any]] = None
    after: Optional[Dict[str, Any]] = None
    diff: Optional[Dict[str, Any]] = None

@dataclass
class DryRunResult:
    ok: bool = True
    dry_run: bool = True
    changes: List[PlannedChange] = None
    summary: Dict[str, int] = None

    def __post_init__(self):
        if self.changes is None:
            self.changes = []
        if self.summary is None:
            self.summary = {"create": 0, "update": 0, "delete": 0, "noop": 0}

def compute_dry_run(desired_state: Dict, actual_state: Dict) -> DryRunResult:
    result = DryRunResult()

    # Check for creates and updates
    for key, desired in desired_state.items():
        actual = actual_state.get(key)

        if actual is None:
            result.changes.append(PlannedChange(
                action=ChangeAction.CREATE,
                resource_type=desired['type'],
                resource_id=key,
                after=desired
            ))
            result.summary['create'] += 1
        elif actual != desired:
            result.changes.append(PlannedChange(
                action=ChangeAction.UPDATE,
                resource_type=desired['type'],
                resource_id=key,
                before=actual,
                after=desired,
                diff=compute_diff(actual, desired)
            ))
            result.summary['update'] += 1

    # Check for deletes
    for key in actual_state:
        if key not in desired_state:
            result.changes.append(PlannedChange(
                action=ChangeAction.DELETE,
                resource_type=actual_state[key]['type'],
                resource_id=key,
                before=actual_state[key]
            ))
            result.summary['delete'] += 1

    return result
```

<!-- src: audit-agentic-cli/references/examples.md#7. Auth Credential Resolution (Python) -->
## Auth credential resolution

```python
import os
import sys
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

@dataclass
class Credential:
    token: str
    source: str  # 'stdin', 'file', 'env', 'config', 'keychain', 'oidc'

class AuthError(Exception):
    exit_code = 4  # the CLI's top-level handler exits with this, class "auth"

def resolve_credential(
    flag_token_file: Optional[str] = None,
    flag_token_stdin: bool = False
) -> Credential:
    """
    Resolve credentials in priority order:
    1. Flags: --token-file or --token-stdin (never a secret value on argv)
    2. Environment variable (MYCLI_TOKEN)
    3. Project config, then user config
    4. OS credential store / credential helper
    5. OIDC/workload identity
    """

    # 1. Stdin (most secure for automation)
    if flag_token_stdin:
        token = sys.stdin.read().strip()
        return Credential(token=token, source='stdin')

    # 1. Token file
    if flag_token_file:
        token = Path(flag_token_file).read_text().strip()
        return Credential(token=token, source='file')

    # 2. Environment variable
    env_token = os.environ.get('MYCLI_TOKEN')
    if env_token:
        return Credential(token=env_token, source='env')

    # 3. Config (project, then user)
    config_token = load_config_token()
    if config_token:
        return Credential(token=config_token, source='config')

    # 4. Keychain
    keychain_token = get_keychain_token()
    if keychain_token:
        return Credential(token=keychain_token, source='keychain')

    # 5. OIDC / workload identity
    oidc_token = get_workload_identity_token()
    if oidc_token:
        return Credential(token=oidc_token, source='oidc')

    raise AuthError("No credentials found. Run 'mycli auth login' first.")  # exit 4
```

> Note: the token is never accepted as an argv value (it would be visible in `ps`); OIDC is implemented, and credentials follow the one precedence order.
