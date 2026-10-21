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
  error?: { class?: string; code: string; message: string; retryable?: boolean; details?: Record<string, unknown> };
  exit_code?: number; // set on failure: the process exit code from the one table
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
    const e = error as { code?: number | string | null; signal?: string; killed?: boolean; stdout?: string; stderr?: string };
    if (e.killed === true) { // our own timeout killed the process (every execFile error has a `killed` field, true or false)
      return { ok: false, error: { code: 'timeout', message: 'Command timed out', retryable: true }, exit_code: 7 };
    }
    // a child killed by a signal has code null: map it to 130 (SIGINT) or 143 (SIGTERM)
    const exit = typeof e.code === 'number' ? e.code : e.signal === 'SIGINT' ? 130 : e.signal === 'SIGTERM' ? 143 : 1;
    // In --json mode the failure envelope is on stdout (cli/envelope-and-errors.md): prefer it
    try {
      if (e.stdout?.trim()) return { ...JSON.parse(e.stdout), exit_code: exit };
    } catch { /* not JSON: fall back to the exit code */ }
    return {
      ok: false,
      error: {
        code: `exit_${exit}`,
        message: e.stderr?.trim() || 'Unknown error',
        retryable: exit === 7, // exit 7 is the transient group
      },
      exit_code: exit,
    };
  }
}

// Usage
const result = await invokeCLI(['mycli', 'task', 'start', 'prompt.md'], { timeout: 60000 });
```

> Note: use `execFile` with an argument array, never a joined shell string, so an argument cannot inject shell syntax. A failed command's envelope is on stdout, so read `stdout` from the thrown error before falling back to `exit_<n>`; `retryable` follows the exit code (7).

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
    stdio: ['ignore', 'pipe', 'inherit'], // stderr is human diagnostics: pass it through, never leave a pipe unread
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

  let finished = false;
  for await (const event of streamTaskEvents(taskId)) {
    switch (event.type) {
      case 'approval':
        // Handle approval request
        const reqId = (event.data as { req_id: string }).req_id;
        await invokeCLI(['mycli', 'request', 'answer', reqId, '--yes', '--json']);
        break;
      case 'complete':
        console.log('Task completed:', event.data);
        finished = true;
        break;
      case 'error':
        throw new Error(`Task failed: ${JSON.stringify(event.data)}`);
    }
    if (finished) break;
  }
  if (!finished) throw new Error('Event stream ended before a complete or error event');
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
