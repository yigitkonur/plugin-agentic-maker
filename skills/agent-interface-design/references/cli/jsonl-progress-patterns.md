# JSONL Progress Patterns

> Read when: you are choosing how a streaming command reports percentage, item-count, multi-phase or heartbeat progress.

<!-- src: audit-agentic-cli/references/output-contracts.md#Progress Event Patterns -->
## Progress event patterns

The sequences below show events in the order they occur. In a real run the `progress`, `phase` and `heartbeat` lines go to stderr and the terminal `completed` line goes to stdout (see `streams-and-jsonl.md`). Opening line of the minimal form:

```jsonl
{"type":"progress","phase":"downloading","percent":25,"message":"Downloading dependencies..."}
{"type":"progress","phase":"downloading","percent":50}
{"type":"progress","phase":"building","percent":75}
{"type":"completed","status":"succeeded","result":{"id":"build_123"}}
```

### Percentage-based progress

```jsonl
{"type":"progress","phase":"upload","percent":0,"message":"Starting upload...","timestamp":"2024-01-15T10:30:00Z"}
{"type":"progress","phase":"upload","percent":25,"message":"Uploading file 1/4","timestamp":"2024-01-15T10:30:05Z"}
{"type":"progress","phase":"upload","percent":50,"message":"Uploading file 2/4","timestamp":"2024-01-15T10:30:10Z"}
{"type":"progress","phase":"upload","percent":75,"message":"Uploading file 3/4","timestamp":"2024-01-15T10:30:15Z"}
{"type":"progress","phase":"upload","percent":100,"message":"Upload complete","timestamp":"2024-01-15T10:30:20Z"}
```

### Item-based progress (unknown total)

```jsonl
{"type":"progress","phase":"scan","items_processed":0,"message":"Starting scan..."}
{"type":"progress","phase":"scan","items_processed":150,"message":"Scanning files..."}
{"type":"progress","phase":"scan","items_processed":423,"message":"Scanning files..."}
{"type":"completed","status":"succeeded","result":{"files_scanned":423,"issues_found":12}}
```

### Multi-phase progress

```jsonl
{"type":"phase","phase":"download","status":"started","timestamp":"2024-01-15T10:30:00Z"}
{"type":"progress","phase":"download","percent":50}
{"type":"phase","phase":"download","status":"completed","duration_ms":5000}
{"type":"phase","phase":"extract","status":"started"}
{"type":"progress","phase":"extract","percent":30}
{"type":"phase","phase":"extract","status":"completed","duration_ms":2000}
{"type":"phase","phase":"install","status":"started"}
{"type":"progress","phase":"install","percent":80}
{"type":"phase","phase":"install","status":"completed","duration_ms":8000}
{"type":"completed","status":"succeeded","result":{"installed":"package@1.2.3"}}
```

### Long-running operations with heartbeat

Emit a `heartbeat` every 30s.

```jsonl
{"type":"progress","phase":"training","percent":0,"eta_seconds":3600}
{"type":"heartbeat","timestamp":"2024-01-15T10:30:30Z","uptime_ms":30000}
{"type":"progress","phase":"training","percent":5,"eta_seconds":3420}
{"type":"heartbeat","timestamp":"2024-01-15T10:31:00Z","uptime_ms":60000}
{"type":"progress","phase":"training","percent":10,"eta_seconds":3240}
```
