# Node/TypeScript: Calling a CLI from an Agent

> Read when: you are writing the TypeScript wrapper that runs a CLI with `child_process`: JSON invocation, retry with backoff, JSONL streaming with `spawn`, and a class-based wrapper.

The rules are in `../../cli/caller-integration.md`. Resilience patterns: `agent-integration-resilience.md`. Provider tool definitions: `agent-integration-frameworks.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#10. TypeScript/JavaScript Integration | audit-agentic-cli/references/agent-integration.md#Basic child_process Invocation -->
## Basic child_process invocation

```typescript
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);

interface CLIResult {
  ok: boolean;
  result?: Record<string, unknown>;
  error?: { code: string; message: string; retryable?: boolean };
}

/**
 * Invoke CLI with JSON output and proper timeout handling.
 */
async function invokeCLI(
  cmd: string[],
  options: { timeout?: number; cwd?: string; env?: Record<string, string> } = {}
): Promise<CLIResult> {
  const { timeout = 30000, cwd, env } = options;
  const [bin, ...args] = [...cmd, '--json', '--quiet'];

  try {
    const { stdout } = await execFileAsync(bin, args, {
      timeout,
      cwd,
      env: { ...process.env, ...env, NO_COLOR: '1' },
    });

    if (stdout.trim()) {
      return JSON.parse(stdout);
    }
    return { ok: true };
  } catch (error: unknown) {
    const e = error as { code?: number | string; killed?: boolean; stdout?: string; stderr?: string };
    if (e.killed === true) { // our own timeout killed the process (every execFile error has a `killed` field, true or false)
      return { ok: false, error: { code: 'timeout', message: 'Command timed out', retryable: true } };
    }
    // In --json mode the failure envelope is on stdout (cli/envelope-and-errors.md): prefer it
    try {
      if (e.stdout?.trim()) return JSON.parse(e.stdout);
    } catch { /* not JSON: fall back to the exit code */ }
    return {
      ok: false,
      error: {
        code: `exit_${e.code ?? 1}`,
        message: e.stderr?.trim() || 'Unknown error',
        retryable: e.code === 7, // exit 7 is the transient group
      },
    };
  }
}

// Usage
const result = await invokeCLI(['mycli', 'task', 'start', 'prompt.md'], { timeout: 60000 });
```

> Reconciled: the source joined the arguments into one shell string for `exec`, which lets an argument inject shell syntax; this file uses `execFile` with an argument array. It also adds the `env` option that the tracing example passes. A failed command's envelope is on stdout, so the sample reads `stdout` from the thrown error before falling back to `exit_<n>`; `retryable` follows the exit code (7).

<!-- src: audit-agentic-cli/references/agent-integration.md#Async/Await with Retry -->
## Async/await with retry

```typescript
import { setTimeout } from 'timers/promises';

async function invokeWithRetry(
  cmd: string[],
  options: { maxRetries?: number; baseDelay?: number; timeout?: number } = {}
): Promise<CLIResult> {
  const { maxRetries = 3, baseDelay = 1000, timeout } = options;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const result = await invokeCLI(cmd, { timeout });

    if (result.ok) return result;
    if (!result.error?.retryable) return result;
    if (attempt === maxRetries) return result;

    const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
    await setTimeout(delay);
  }

  return { ok: false, error: { code: 'exhausted', message: 'Max retries exceeded' } };
}
```

<!-- src: audit-agentic-cli/references/agent-integration.md#JSONL Streaming with spawn -->
## JSONL streaming with spawn

```typescript
import { spawn } from 'child_process';
import { createInterface } from 'readline';

interface TaskEvent {
  type: 'status' | 'output' | 'approval' | 'complete' | 'error';
  task_id?: string;
  data?: unknown;
}

/**
 * Stream JSONL events from CLI task follow command.
 */
async function* streamTaskEvents(
  taskId: string,
  options: { signal?: AbortSignal } = {}
): AsyncGenerator<TaskEvent> {
  const proc = spawn('mycli', ['task', 'follow', taskId, '--json'], {
    stdio: ['ignore', 'pipe', 'pipe'],
    signal: options.signal,
  });

  const rl = createInterface({ input: proc.stdout });

  try {
    for await (const line of rl) {
      if (!line.trim()) continue;
      try {
        yield JSON.parse(line) as TaskEvent;
      } catch {
        console.error('Invalid JSONL:', line);
      }
    }
  } finally {
    rl.close();
    proc.kill();
  }
}

// Usage with async iteration
async function runTask(promptFile: string): Promise<void> {
  const start = await invokeCLI(['mycli', 'task', 'start', promptFile, '--json']);
  if (!start.ok) throw new Error(start.error?.message);

  const taskId = (start.result as { task_id: string }).task_id;

  for await (const event of streamTaskEvents(taskId)) {
    switch (event.type) {
      case 'approval':
        // Handle approval request
        await invokeCLI(['mycli', 'request', 'answer', event.data?.req_id, '--yes', '--json']);
        break;
      case 'complete':
        console.log('Task completed:', event.data);
        return;
      case 'error':
        throw new Error(`Task failed: ${JSON.stringify(event.data)}`);
    }
  }
}
```

<!-- src: audit-agentic-cli/references/agent-integration.md#Class-based CLI Wrapper -->
## Class-based CLI wrapper

```typescript
import { EventEmitter } from 'events';

class CLIAgent extends EventEmitter {
  private baseCmd: string[];
  private defaultFlags: string[];

  constructor(cli: string, defaultFlags: string[] = ['--json', '--quiet']) {
    super();
    this.baseCmd = [cli];
    this.defaultFlags = defaultFlags;
  }

  async invoke(subcommand: string[], extraFlags: string[] = [], retry: { timeout?: number } = {}): Promise<CLIResult> {
    const cmd = [...this.baseCmd, ...subcommand, ...this.defaultFlags, ...extraFlags];
    const result = await invokeWithRetry(cmd, retry);
    this.emit('invocation', { cmd, result });
    return result;
  }

  async taskStart(promptFile: string, opts: { session?: string; timeout?: number } = {}) {
    const flags = [];
    if (opts.session) flags.push('--session', opts.session);
    if (opts.timeout) flags.push('--timeout', String(opts.timeout));
    return this.invoke(['task', 'start', promptFile], flags);
  }

  async taskWait(taskId: string, timeoutMs = 300000) {
    // the process timeout sits a little above the CLI's own wait, so the CLI reports its timeout itself
    return this.invoke(['task', 'wait', taskId, '--timeout', String(timeoutMs / 1000)], [], { timeout: timeoutMs + 5000 });
  }
}
```
