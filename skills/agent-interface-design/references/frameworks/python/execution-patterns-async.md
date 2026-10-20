# Python: Graceful Shutdown on Signals

> Read when: you are implementing SIGINT/SIGTERM handling with a grace period in a long-running Python CLI.

## Graceful shutdown

Contract: `../../cli/timeouts-and-signals.md`.

```python
import signal
import sys
from contextlib import contextmanager

class GracefulShutdown:
    def __init__(self, grace_period: float = 30.0):
        self.grace_period = grace_period
        self.shutting_down = False

    def __enter__(self):
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)
        return self

    def __exit__(self, *args):
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

    def _handle_signal(self, signum, frame):
        if self.shutting_down:
            # Second signal - force exit
            sys.exit(1)

        self.shutting_down = True
        print(f"\nReceived signal {signum}, shutting down gracefully...", file=sys.stderr)

        # Schedule force exit
        signal.alarm(int(self.grace_period))

    def check(self):
        """Check if shutdown requested. Call periodically in long operations."""
        if self.shutting_down:
            raise KeyboardInterrupt("Shutdown requested")

# Usage
with GracefulShutdown() as shutdown:
    for i in range(100):
        shutdown.check()  # Raises if shutdown requested
        do_work(i)
```
