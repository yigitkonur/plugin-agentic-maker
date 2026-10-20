# Hash execution state to stop reprocessing loops

> Read when: an agent keeps re-downloading, re-parsing or re-processing the same file or query, or you are adding a short-lived result cache to a tool.

<!-- src: audit-agentic-mcp/references/patterns/testing.md#6. Use File Hashing to Prevent Agent Reprocessing Loops -->
## Cache by execution state

Hash the full execution state, not just the action, so the agent can detect "I already downloaded and parsed this exact file 30 seconds ago." This kills the common loop where agents re-download, re-parse or re-process the same data repeatedly.

The server-side execution cache: build a key as a SHA-256 over the tool name plus all params (sorted keys), keep entries for `CACHE_TTL = 60` seconds, and on a hit inside the TTL return the cached result with `cached: true` and a note ("Cached Ns ago. Use force_refresh=true to bypass."). On a miss or when `force_refresh` is set, run the tool and store the result with a timestamp. Python code: `../frameworks/mcp-python/testing.md`.

Hash these inputs: tool name, all parameters, file URLs/paths, filter/query values.

Do not hash: timestamps, request IDs, auth tokens, pagination cursors.

The `force_refresh` escape hatch: always expose it as an optional boolean parameter (default `false`) and say so in the description:

```json
{
  "name": "download_report",
  "description": "Downloads and parses the report. Cached 60s. Use force_refresh=true for fresh data.",
  "inputSchema": {
    "properties": {
      "url": { "type": "string" },
      "force_refresh": { "type": "boolean", "default": false }
    }
  }
}
```

For multi-level caches of upstream responses, see `ops-rate-limiting-and-caching.md`.

Sources: r/AI_Agents discussion, MotherDuck (dev diary on building MCP).
