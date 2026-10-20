# Node.js: Idempotency Keys and Retry

> Read when: you are implementing idempotent creates or retry with backoff and Retry-After in a Node.js / TypeScript CLI.

## Idempotency manager

Contract: `../../cli/idempotency.md`. Cached results live 24 hours.

```typescript
import { mkdirSync, readFileSync, writeFileSync } from 'fs';
import { homedir } from 'os';
import { join } from 'path';

interface IdempotencyResult<T> {
  cached: boolean;
  result: T;
}

type Entry = { result: unknown; expiry: number };

class IdempotencyManager {
  // One CLI process serves one command, and a retried `create` is a new process: the cache must outlive it.
  private dir = join(homedir(), '.cache', 'mycli');
  private file = join(this.dir, 'idempotency.json');
  private ttlMs = 24 * 60 * 60 * 1000; // 24 hours

  private load(): Record<string, Entry> {
    try { return JSON.parse(readFileSync(this.file, 'utf8')); } catch { return {}; }
  }

  async executeIdempotent<T>(
    key: string,
    operation: () => Promise<T>
  ): Promise<IdempotencyResult<T>> {
    const cache = this.load();
    const cached = cache[key];
    if (cached && cached.expiry > Date.now()) {
      return { cached: true, result: cached.result as T };
    }

    const result = await operation();

    cache[key] = { result, expiry: Date.now() + this.ttlMs };
    mkdirSync(this.dir, { recursive: true });
    writeFileSync(this.file, JSON.stringify(cache));

    return { cached: false, result };
  }
}

// CLI command
program
  .command('create')
  .option('--idempotency-key <key>', 'Idempotency key for safe retry')
  .option('--name <name>', 'Resource name')
  .action(async (options) => {
    const idempotency = new IdempotencyManager();

    const { result } = options.idempotencyKey
      ? await idempotency.executeIdempotent(
          options.idempotencyKey,
          () => api.createResource(options.name)
        )
      : { result: await api.createResource(options.name) };

    console.log(JSON.stringify(result));
  });
```

<!-- src: audit-agentic-cli/references/execution-patterns.md#Node.js Retry Implementation -->
## Retry

Contract and defaults: `../../cli/retry.md`.

```typescript
// maxAttempts counts total attempts (the rate limiter's maxRetries counts retries after the first)
interface RetryConfig {
  maxAttempts: number;
  initialBackoffMs: number;
  maxBackoffMs: number;
  backoffFactor: number;
  jitter: number;
  isRetryable?: (error: Error) => boolean;
}

const defaultConfig: RetryConfig = {
  maxAttempts: 5,
  initialBackoffMs: 100,
  maxBackoffMs: 30000,
  backoffFactor: 2,
  jitter: 0.2,
  isRetryable: (error) => {
    // Default: retry network errors (node-fetch FetchError, native fetch TypeError) and 429/5xx
    if (error.name === 'FetchError' || error instanceof TypeError) return true;
    if ('status' in error) {
      const status = (error as any).status;
      return status === 429 || (status >= 500 && status < 600);
    }
    return false;
  },
};

async function withRetry<T>(
  operation: () => Promise<T>,
  config: Partial<RetryConfig> = {}
): Promise<T> {
  const cfg = { ...defaultConfig, ...config };
  let lastError: Error;

  for (let attempt = 0; attempt < cfg.maxAttempts; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error as Error;

      if (!cfg.isRetryable!(lastError)) {
        throw error;
      }

      // Check for Retry-After header
      let backoffMs: number;
      const retryAfter = (error as any).response?.headers?.get?.('retry-after');
      if (retryAfter) {
        const secs = Number(retryAfter); // delta-seconds, or an HTTP-date
        backoffMs = Number.isFinite(secs) ? secs * 1000 : Math.max(0, Date.parse(retryAfter) - Date.now());
      } else {
        backoffMs = Math.min(
          cfg.initialBackoffMs * Math.pow(cfg.backoffFactor, attempt),
          cfg.maxBackoffMs
        );
        // Add jitter
        const jitter = backoffMs * cfg.jitter * (Math.random() * 2 - 1);
        backoffMs += jitter;
      }

      await new Promise((resolve) => setTimeout(resolve, backoffMs));
    }
  }

  throw new Error(`Retry exhausted after ${cfg.maxAttempts} attempts: ${lastError!.message}`);
}

// Usage
// Native fetch resolves on 429 and 5xx instead of throwing, so turn those into errors the retry loop can see
const result = await withRetry(async () => {
  const res = await fetch(`${API_URL}/resources`, { method: 'POST', body: JSON.stringify({ name }) });
  if (res.status === 429 || res.status >= 500) {
    throw Object.assign(new Error(`HTTP ${res.status}`), { status: res.status, response: res });
  }
  return res;
}, { maxAttempts: 3 });
```
