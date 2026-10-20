# Rate-limit per tool category and cache reads in levels

> Read when: agents hammer an MCP server or its upstream API, or one global rate limit is either too strict for reads or too loose for expensive calls.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#9. Token Bucket Rate Limiting per Tool Category -->
## Use one token bucket per tool category

Do not apply a single global rate limit. Different tool categories have radically different cost profiles; use per-category token buckets. Each bucket has a `capacity` (max tokens) and a `refillRate` (tokens added per second); a call consumes a cost (default 1), and the bucket exposes a retry-after value. Map every tool name to a category and wrap its handler.

Recommended starting limits:

| Category | Capacity | Refill Rate | Rationale |
|---|---|---|---|
| read | 120 | 10/s | Local cache; near-free |
| write | 30 | 2/s | DB writes; moderate cost |
| ai | 10 | 0.5/s | LLM inference; expensive |
| external_api | 20 | 1/s | Third-party rate limits |

When a bucket is empty return a tool error (`isError: true`) the agent can act on:

```json
{
  "error_category": "RATE_LIMITED",
  "message": "Rate limit for write tools exceeded.",
  "retryable": true,
  "retry_after_ms": 500,
  "suggested_actions": ["wait_and_retry"]
}
```

Why: flat global limits either over-restrict cheap reads or under-protect expensive AI calls. Categorical buckets let you tune each independently and surface informative retry-after values. Example mapping: `search_files`, `list_resources` read; `update_record`, `create_issue` write; `analyze_code`, `summarize` ai. Code: [typescript](../frameworks/mcp-ts/transport-and-ops-rate-limiting.md).

Sources: community discussion on production throttling, Docker blog.

<!-- src: audit-agentic-mcp/references/patterns/transport-and-ops.md#10. Multi-Level Caching for MCP Responses -->
## Cache read tools in three levels

Tool calls that read data frequently return the same result within a session. A three-level hierarchy removes redundant upstream calls without serving stale data:

- L1: in-process LRU memory (about 500 entries, 60 s TTL): fastest, session-local.
- L2: Redis: shared across instances, survives restarts.
- L3: persistent DB cache for expensive computations such as embeddings (24 hours).

Lookup order is L1, then L2 (warm L1 on a hit), then the upstream call; write to L1 and L2 with the TTL for that data type. Wrap any read tool in a cached handler keyed by a cache key.

Cache TTL strategy by data type:

| Data Type | L1 TTL | L2 TTL | Notes |
|---|---|---|---|
| Repo file tree | 30s | 5min | Changes infrequently mid-session |
| Search results | 60s | 10min | Queries repeat in agentic loops |
| User profile | 5min | 1hr | Rarely changes |
| Embeddings / AI analysis | N/A (skip L1) | 24hr | Expensive to recompute |
| Live metrics / status | 5s | 30s | Must be near-real-time |

Cache key design: include the version or ETag when available, for example `github:issues:<owner>/<repo>:<etag>`.

Why: agentic loops repeatedly call the same tools with identical params; without caching, a 10-step workflow that queries file listings on each step can generate 10x the upstream API calls needed. For deduplicating repeated identical calls inside a session see [ops-execution-cache.md](ops-execution-cache.md). Code: [typescript](../frameworks/mcp-ts/transport-and-ops-caching.md).

Sources: community discussion of GitHub server rate-limit mitigation, Docker blog.
