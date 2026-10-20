# TypeScript: per-category token bucket rate limiter

> Read when: you are implementing the per-category rate limiter for an MCP server in TypeScript.

Rules, limits table and error shape: [ops-rate-limiting-and-caching.md](../../mcp/ops-rate-limiting-and-caching.md).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#9. Token Bucket Rate Limiting per Tool Category -->
## Token bucket and category wrapper

```typescript
interface BucketConfig {
  capacity: number;    // Max tokens in bucket
  refillRate: number;  // Tokens added per second
}

class TokenBucket {
  private tokens: number;
  private lastRefill: number;

  constructor(private config: BucketConfig) {
    this.tokens = config.capacity;
    this.lastRefill = Date.now();
  }

  consume(cost = 1): boolean {
    const now = Date.now();
    const elapsed = (now - this.lastRefill) / 1000;
    this.tokens = Math.min(this.config.capacity, this.tokens + elapsed * this.config.refillRate);
    this.lastRefill = now;

    if (this.tokens < cost) return false;
    this.tokens -= cost;
    return true;
  }

  get retryAfterMs(): number {
    return Math.ceil(((1 - this.tokens) / this.config.refillRate) * 1000);
  }
}

const rateLimiters: Record<string, TokenBucket> = {
  read:  new TokenBucket({ capacity: 120, refillRate: 10 }), // generous: cheap reads
  write: new TokenBucket({ capacity: 30,  refillRate: 2  }), // moderate: writes have side effects
  ai:    new TokenBucket({ capacity: 10,  refillRate: 0.5 }), // tight: AI calls are expensive
};

const toolCategory: Record<string, keyof typeof rateLimiters> = {
  search_files:   "read",
  list_resources: "read",
  update_record:  "write",
  create_issue:   "write",
  analyze_code:   "ai",
  summarize:      "ai",
};

function withRateLimit(category: string, handler: Function) {
  return async (...args: any[]) => {
    const bucket = rateLimiters[category];
    if (bucket && !bucket.consume()) {
      return {
        content: [{ type: "text", text: JSON.stringify({
          error_category: "RATE_LIMITED",
          message: `Rate limit for ${category} tools exceeded.`,
          retryable: true,
          retry_after_ms: bucket.retryAfterMs,
          suggested_actions: ["wait_and_retry"],
        }) }],
        isError: true,
      };
    }
    return handler(...args);
  };
}
```
