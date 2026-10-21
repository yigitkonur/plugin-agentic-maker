# Shared Event Log and Workflow Stages in TypeScript

> Read when: you are coordinating several agents through an append-only log or rejecting out-of-order tool calls with stage gates in TypeScript.

Explanation and rules: ../../mcp/patterns-guarded-workflows.md and ../../mcp/patterns-error-taxonomy-and-event-log.md

## Pattern 5: Shared Context: Append-Only Event Log for Multi-Agent Coordination

```typescript
interface LogEntry {
  id: string;
  agent_id: string;
  timestamp: string;          // ISO 8601
  type: "observation" | "decision" | "action" | "result" | "handoff";
  payload: unknown;
  confidence?: number;        // 0.0-1.0, optional
  supersedes?: string;        // ID of a previous entry this revises
}

// In-memory log (replace with Redis or Postgres for persistence)
const eventLog: LogEntry[] = [];

server.tool("log_event", "Append an event to the shared coordination log", {
  agent_id: z.string(),
  type: z.enum(["observation", "decision", "action", "result", "handoff"]),
  payload: z.unknown(),
  confidence: z.number().min(0).max(1).optional(),
  supersedes: z.string().optional().describe("ID of a prior log entry this entry revises"),
}, async ({ agent_id, type, payload, confidence, supersedes }) => {
  const entry: LogEntry = {
    id: crypto.randomUUID(),
    agent_id,
    timestamp: new Date().toISOString(),
    type,
    payload,
    confidence,
    supersedes,
  };
  eventLog.push(entry);
  return { content: [{ type: "text", text: `Logged event ${entry.id}` }] };
});

server.tool("read_log", "Read shared coordination log, optionally filtered", {
  since: z.string().optional().describe("ISO timestamp -- only return entries after this time"),
  agent_id: z.string().optional().describe("Filter to a specific agent's entries"),
  type: z.string().optional().describe("Filter to a specific event type"),
  limit: z.number().int().min(1).default(50),
}, async ({ since, agent_id, type, limit }) => {
  let entries = eventLog;
  if (since) entries = entries.filter(e => e.timestamp > since);
  if (agent_id) entries = entries.filter(e => e.agent_id === agent_id);
  if (type) entries = entries.filter(e => e.type === type);
  return { content: [{ type: "text", text: JSON.stringify(entries.slice(-limit), null, 2) }] };
});
```

## Pattern 6: Server-Enforced Workflow Stages

```typescript
type WorkflowStage =
  | "initialized"
  | "data_loaded"
  | "analysis_complete"
  | "changes_validated"
  | "committed";

const STAGE_ORDER: WorkflowStage[] = [
  "initialized", "data_loaded", "analysis_complete", "changes_validated", "committed"
];

const sessions = new Map<string, WorkflowStage>();

function assertStage(sessionId: string, required: WorkflowStage, allowedPrevious: WorkflowStage[]) {
  const current = sessions.get(sessionId) ?? "initialized";
  if (!allowedPrevious.includes(current)) {
    const next = STAGE_ORDER[STAGE_ORDER.indexOf(current) + 1];
    throw {
      message: `Stage gate: current stage is "${current}". Must complete "${next}" before calling this tool.`,
      current_stage: current,
      required_stage: required,
      next_required_tool: stageToTool[current],
    };
  }
}

const stageToTool: Record<WorkflowStage, string> = {
  initialized: "load_data",
  data_loaded: "analyze_data",
  analysis_complete: "validate_changes",
  changes_validated: "commit_changes",
  committed: "(workflow complete)",
};

server.tool("commit_changes", "Commit validated changes. Requires validation stage.", {
  session_id: z.string(),
  dry_run: z.boolean().default(false),
}, async ({ session_id, dry_run }) => {
  try {
    assertStage(session_id, "committed", ["changes_validated"]);
  } catch (e: any) {
    return { content: [{ type: "text", text: JSON.stringify(e) }], isError: true };
  }

  const result = await commitChanges(session_id, dry_run);
  if (!dry_run) sessions.set(session_id, "committed"); // a dry run must not consume the stage
  return { content: [{ type: "text", text: `Changes committed. ${result.summary}` }] };
});
```
