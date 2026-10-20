# Python: Dry-Run and Non-Interactive Prompts

> Read when: you are implementing `--dry-run` or TTY-aware confirm and prompt helpers in a Python (Click) CLI.

## Dry-run

Contract: `../../cli/dry-run.md`. This section carries the Python half of the dry-run implementation; the Go half is in the Go file of the same name.

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

class DryRunMode(Enum):
    NONE = None
    CLIENT = "client"
    SERVER = "server"

@dataclass
class Change:
    action: str  # create, update, delete
    resource_type: str
    resource_id: str
    diff: Optional[Dict[str, Dict[str, Any]]] = None

@dataclass
class ApplyResult:
    ok: bool
    dry_run: bool
    changes: List[Change]
    summary: Dict[str, int]

def apply_resources(
    files: List[str],
    dry_run: DryRunMode = DryRunMode.NONE
) -> ApplyResult:
    resources = load_resources(files)

    if dry_run == DryRunMode.CLIENT:
        return validate_locally(resources)

    response = api.apply(
        resources=resources,
        dry_run=(dry_run == DryRunMode.SERVER)
    )

    return ApplyResult(
        ok=response["ok"],
        dry_run=response.get("dry_run", False),
        changes=[Change(**c) for c in response["changes"]],
        summary=response["summary"]
    )
```

## Interactive detection, prompt and confirm

Contract: `../../cli/non-interactive.md`.

> Reconciled: the source `confirm` returned `default` (False) when non-interactive, then `delete` exited 1 with "Aborted". Here a confirmation that cannot be asked fails with exit 2 naming `--yes` / `--force`, and prompts go to stderr.

```python
import sys
import os
import click

def is_interactive() -> bool:
    """Check if running in interactive mode."""
    # Check environment variable first
    if os.environ.get("MYCLI_NON_INTERACTIVE"):
        return False

    # Check if stdin/stdout are TTYs
    return sys.stdin.isatty() and sys.stdout.isatty()

def prompt(message: str, *, non_interactive: bool = False) -> str:
    """Prompt for input, fail in non-interactive mode."""
    if non_interactive or not is_interactive():
        raise RuntimeError(f"Prompt required in non-interactive mode: {message}")

    print(message, end="", file=sys.stderr)
    return input()

def confirm(
    message: str,
    *,
    non_interactive: bool = False,
    auto_yes: bool = False,
) -> bool:
    """Confirm action with user. Exit 2 if it cannot be asked."""
    if auto_yes:
        return True

    if non_interactive or not is_interactive():
        print(f"Confirmation required: {message}. Re-run with --yes or --force.", file=sys.stderr)
        sys.exit(2)

    print(f"{message} [y/N]: ", end="", file=sys.stderr)
    response = input().strip().lower()
    return response == "y"

# CLI integration
@click.command()
@click.option('--non-interactive', is_flag=True, envvar='MYCLI_NON_INTERACTIVE')
@click.option('--yes', '-y', is_flag=True, help='Auto-confirm prompts')
@click.option('--force', '-f', is_flag=True, help='Bypass safety checks')
def delete(non_interactive: bool, yes: bool, force: bool):
    if not force:
        if not confirm("This will delete all data. Continue?",
                      non_interactive=non_interactive, auto_yes=yes):
            click.echo("Aborted", err=True)
            sys.exit(2)  # confirmation not given: same code as the non-interactive refusal (../../cli/non-interactive.md)

    # Proceed with deletion
```
