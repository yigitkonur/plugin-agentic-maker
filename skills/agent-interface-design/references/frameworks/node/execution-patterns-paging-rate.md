# Node.js: Async-Iterator Pagination and Token-Bucket Rate Limiter

> Read when: you are implementing `--all` cursor pagination or a token-bucket rate limiter with circuit breaker in a Node.js / TypeScript CLI.

## Async-iterator pagination

Contract: `../../cli/pagination.md` (`result.items`, `result.next_cursor`, `result.has_more`, optional `result.total`).

> Reconciled: the source used `data`, `pagination.hasNext`, `totalCount`; the code uses `items`, `hasMore`, `nextCursor`, `total`, serialized flat as `has_more`, `next_cursor`.

```typescript
// Assumed from your app: program (Commander), api, Item.
interface PaginationOptions {
  perPage?: number; cursor?: string; page?: number;
  sortBy?: string; sortOrder?: 'asc' | 'desc';
}

interface Page<T> {
  items: T[];
  total?: number;
  hasMore: boolean;     // serialized as has_more, flat in result
  nextCursor?: string;  // serialized as next_cursor
}

async function* fetchAllPages<T>(
  fetchFn: (opts: PaginationOptions) => Promise<Page<T>>,
  options: { perPage?: number; maxPages?: number; onCapped?: () => void } = {}
): AsyncGenerator<T> {
  const perPage = options.perPage ?? 100;
  const maxPages = options.maxPages ?? 100;
  let cursor: string | undefined;
  let pagesFetched = 0;

  while (pagesFetched < maxPages) {
    const page = await fetchFn({ perPage, cursor });

    for (const item of page.items) {
      yield item;
    }

    pagesFetched++;

    if (!page.hasMore) return;
    cursor = page.nextCursor;
  }
  options.onCapped?.(); // the page cap stopped the loop
}

// CLI command
program
  .command('list')
  .option('--per-page <n>', 'Items per page', '50')
  .option('--cursor <token>', 'Pagination cursor')
  .option('--page <n>', 'Page number')
  .option('--all', 'Fetch all pages')
  .option('--max-pages <n>', 'Max pages for --all', '100')
  .option('--sort-by <field>', 'Sort field', 'created_at')
  .option('--sort-order <order>', 'Sort order', 'desc')
  .action(async (options) => {
    if (options.all) {
      const items: Item[] = [];
      let truncated = false;
      for await (const item of fetchAllPages(
        (opts) => api.listItems(opts),
        { perPage: parseInt(options.perPage), maxPages: parseInt(options.maxPages), onCapped: () => { truncated = true; } }
      )) {
        items.push(item);
      }
      // page cap hit: has_more true, meta.truncated set
      console.log(JSON.stringify({ ok: true, command: 'list', schema_version: '1.0',
        result: { items, total: items.length, has_more: truncated }, meta: { truncated } }));
    } else {
      const result = await api.listItems({
        perPage: parseInt(options.perPage), cursor: options.cursor,
        page: options.page ? parseInt(options.page) : undefined,
        sortBy: options.sortBy, sortOrder: options.sortOrder,
      });
      console.log(JSON.stringify({ ok: true, command: 'list', schema_version: '1.0',
        result: { items: result.items, has_more: result.hasMore, next_cursor: result.nextCursor, total: result.total }, meta: {} }));
    }
  });
```

## Token-bucket rate limiter

Contract: `../../cli/rate-limits.md`.

```typescript
// Assumed: sleep(ms) = new Promise((r) => setTimeout(r, ms)).
class RateLimitError extends Error { retryAfter?: number; }
class CircuitOpenError extends Error {}
class MaxRetriesExceeded extends Error {}

interface RateLimitOptions {
  rateLimit: string; retryOnRateLimit: boolean; maxRetries: number;
  backoffInitial: number; backoffMax: number; backoffMultiplier: number; backoffJitter: number;
  respectRetryAfter: boolean; circuitBreakerThreshold: number; circuitBreakerTimeout: number;
}

class RateLimiter {
  private tokens: number; private maxTokens: number;
  private refillInterval: number; private lastRefill: number;
  private failures = 0;
  private circuitOpen = false;
  private circuitOpenAt = 0;

  constructor(private options: RateLimitOptions) {
    const [count, period] = this.parseRateLimit(options.rateLimit);
    this.maxTokens = this.tokens = count;
    this.refillInterval = period;
    this.lastRefill = Date.now();
  }

  private parseRateLimit(rate: string): [number, number] {
    const [count, period] = rate.split('/');
    const periods: Record<string, number> = { second: 1000, minute: 60000, hour: 3600000 };
    return [parseInt(count), periods[period] ?? 60000];
  }

  private refill(): void {
    const now = Date.now();
    this.tokens = Math.min(this.maxTokens, this.tokens + ((now - this.lastRefill) / this.refillInterval) * this.maxTokens);
    this.lastRefill = now;
  }

  private async acquire(): Promise<void> {
    this.refill();
    if (this.tokens < 1) {
      const waitTime = ((1 - this.tokens) / this.maxTokens) * this.refillInterval;
      await sleep(waitTime);
      this.tokens = 1;
    }
    this.tokens -= 1;
  }

  private recordFailure(): void {
    if (++this.failures >= this.options.circuitBreakerThreshold) {
      this.circuitOpen = true;
      this.circuitOpenAt = Date.now();
    }
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.circuitOpen) {
      if (Date.now() - this.circuitOpenAt > this.options.circuitBreakerTimeout) {
        this.circuitOpen = false; this.failures = 0;
      } else {
        throw new CircuitOpenError('Circuit open');
      }
    }

    await this.acquire();

    let backoff = this.options.backoffInitial;
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= this.options.maxRetries; attempt++) {
      try {
        const result = await fn();
        this.failures = 0;
        return result;
      } catch (error) {
        // a 429 uses the retry budget and counts toward the breaker only once it is spent
        if (!(error instanceof RateLimitError)) { this.recordFailure(); throw error; }
        if (!this.options.retryOnRateLimit) throw error;
        let waitTime = this.options.respectRetryAfter && error.retryAfter ? error.retryAfter * 1000 : backoff;
        waitTime += waitTime * this.options.backoffJitter * (Math.random() * 2 - 1);
        await sleep(waitTime);
        backoff = Math.min(backoff * this.options.backoffMultiplier, this.options.backoffMax);
        lastError = error;
      }
    }

    this.recordFailure();
    throw new MaxRetriesExceeded(`Max retries exceeded: ${lastError?.message}`);
  }
}

// CLI
program
  .command('sync')
  .option('--rate-limit <rate>', 'Rate limit', '100/minute')
  .option('--no-retry-on-rate-limit', 'Do not retry on 429')
  .option('--max-retries <n>', 'Max retries', '5')
  .option('--backoff-initial <ms>', 'Initial backoff', '1000')
  .option('--backoff-max <ms>', 'Max backoff', '60000')
  .option('--backoff-multiplier <n>', 'Backoff multiplier', '2')
  .option('--no-respect-retry-after', 'Ignore Retry-After')
  .option('--circuit-breaker-threshold <n>', 'Circuit breaker threshold', '5')
  .option('--circuit-breaker-timeout <ms>', 'Circuit reset timeout', '30000')
  .action(async (options) => {
    const limiter = new RateLimiter({
      rateLimit: options.rateLimit, retryOnRateLimit: options.retryOnRateLimit,
      maxRetries: parseInt(options.maxRetries),
      backoffInitial: parseInt(options.backoffInitial), backoffMax: parseInt(options.backoffMax),
      backoffMultiplier: parseFloat(options.backoffMultiplier), backoffJitter: 0.1,
      respectRetryAfter: options.respectRetryAfter,
      circuitBreakerThreshold: parseInt(options.circuitBreakerThreshold),
      circuitBreakerTimeout: parseInt(options.circuitBreakerTimeout),
    });

    try {
      const result = await limiter.execute(() => api.sync());
      console.log(JSON.stringify({ ok: true, command: 'sync', schema_version: '1.0', result, meta: {} }));
    } catch (err) {
      // transient group: envelope on stdout, human line on stderr, exit 7
      const e = err as Error;
      console.error(e.message);
      console.log(JSON.stringify({ ok: false, schema_version: '1.0', error: {
        class: e instanceof CircuitOpenError ? 'dependency_failed' : 'rate_limit',
        code: e instanceof CircuitOpenError ? 'CIRCUIT_OPEN' : 'RATE_LIMITED', message: e.message, retryable: true } }));
      process.exit(7);
    }
  });
```
