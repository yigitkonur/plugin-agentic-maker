# Node.js: Idempotency Keys and Retry

> Read when: you are implementing idempotent creates or retry with backoff and Retry-After in a Node.js / TypeScript CLI.

## Idempotency manager

Contract: `../../cli/idempotency.md`. Cached results live 24 hours.

```typescript
import { createHash } from 'crypto';

interface IdempotencyResult<T> {
  cached: boolean;
  result: T;
}

class IdempotencyManager {
  private cache: Map<string, { result: unknown; expiry: number }> = new Map();
  private ttlMs = 24 * 60 * 60 * 1000; // 24 hours

  async executeIdempotent<T>(
    key: string,
    operation: () => Promise<T>
  ): Promise<IdempotencyResult<T>> {
    // Check cache
    const cached = this.cache.get(key);
    if (cached && cached.expiry > Date.now()) {
      return { cached: true, result: cached.result as T };
    }

    // Execute operation
    const result = await operation();

    // Cache result
    this.cache.set(key, {
      result,
      expiry: Date.now() + this.ttlMs,
    });

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
    // Default: retry network errors and 5xx
    if (error.name === 'FetchError') return true;
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
        backoffMs = parseInt(retryAfter, 10) * 1000;
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
const result = await withRetry(
  () => fetch(`${API_URL}/resources`, { method: 'POST', body: JSON.stringify({ name }) }),
  { maxAttempts: 3 }
);
```
