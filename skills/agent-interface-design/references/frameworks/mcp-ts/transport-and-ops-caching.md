# TypeScript: three-level cache for tool responses

> Read when: you are implementing the L1/L2 response cache and cached tool wrapper for an MCP server in TypeScript.

Rules, levels and TTL table: [ops-rate-limiting-and-caching.md](../../mcp/ops-rate-limiting-and-caching.md).

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#10. Multi-Level Caching for MCP Responses -->
## Cache class and wrapper

```typescript
import { LRUCache } from "lru-cache";
import Redis from "ioredis";

interface CacheEntry { value: unknown; expiresAt: number; }

class MCPCache {
  // L1: in-process memory -- fastest, session-local
  private l1 = new LRUCache<string, CacheEntry>({ max: 500, ttl: 60_000 });

  // L2: Redis -- shared across instances, survives restarts
  private l2: Redis | null = null;

  // L3: persistent DB cache for expensive computations (e.g., embeddings)
  private l3Ttl = 86_400_000; // 24 hours

  constructor(redisUrl?: string) {
    if (redisUrl) this.l2 = new Redis(redisUrl);
  }

  async get(key: string): Promise<unknown | null> {
    // L1 hit
    const l1 = this.l1.get(key);
    if (l1 && l1.expiresAt > Date.now()) return l1.value;

    // L2 hit
    if (this.l2) {
      const raw = await this.l2.get(key);
      if (raw) {
        const parsed = JSON.parse(raw);
        this.l1.set(key, parsed); // warm L1
        return parsed.value;
      }
    }

    return null;
  }

  async set(key: string, value: unknown, ttlMs: number): Promise<void> {
    const entry = { value, expiresAt: Date.now() + ttlMs };
    this.l1.set(key, entry);
    if (this.l2) {
      await this.l2.set(key, JSON.stringify(entry), "PX", ttlMs);
    }
  }
}

const cache = new MCPCache(process.env.REDIS_URL);

// Wrap any tool with caching
async function cachedToolHandler(cacheKey: string, ttlMs: number, fn: () => Promise<unknown>) {
  const cached = await cache.get(cacheKey);
  if (cached) return cached;
  const result = await fn();
  await cache.set(cacheKey, result, ttlMs);
  return result;
}
```

Cache key design, include version/ETag when available:

```typescript
const key = `github:issues:${owner}/${repo}:${etag}`;
```
