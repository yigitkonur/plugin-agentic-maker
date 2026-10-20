# Structured Error Taxonomy in TypeScript

> Read when: you are returning machine-readable error categories with retry fields from a TypeScript MCP tool.

Explanation and rules: ../../mcp/patterns-error-taxonomy-and-event-log.md. Bounded continuation (Pattern 7): agentic-patterns-continuation.md.

## Pattern 4: SERF: Machine-Readable Error Taxonomy for Agents

```typescript
type SERFCategory =
  | "INVALID_PARAMS"      // Schema/validation failure -- do not retry as-is
  | "RESOURCE_NOT_FOUND"  // Target doesn't exist -- check ID, don't retry
  | "RESOURCE_EXHAUSTED"  // Quota/rate limit -- retry after delay
  | "PERMISSION_DENIED"   // Auth failure -- escalate or try different credentials
  | "RATE_LIMITED"        // Explicit rate limit -- retry after retry_after_ms
  | "INTERNAL_ERROR";     // Server-side failure -- retry with backoff

interface SERFError {
  error_category: SERFCategory;
  message: string;           // Human-readable description
  retryable: boolean;
  retry_after_ms?: number;   // Set for RATE_LIMITED and RESOURCE_EXHAUSTED
  suggested_actions: string[]; // Machine-readable next steps
  param_hints?: Record<string, string>; // For INVALID_PARAMS: field -> fix hint
}

function serfError(category: SERFCategory, message: string, opts: Partial<SERFError> = {}) {
  const defaults: Record<SERFCategory, Partial<SERFError>> = {
    INVALID_PARAMS:     { retryable: false, suggested_actions: ["fix_params_and_retry"] },
    RESOURCE_NOT_FOUND: { retryable: false, suggested_actions: ["search_for_resource", "list_resources"] },
    RESOURCE_EXHAUSTED: { retryable: true,  suggested_actions: ["retry_after_delay", "reduce_request_size"] },
    PERMISSION_DENIED:  { retryable: false, suggested_actions: ["check_permissions", "use_different_credentials"] },
    RATE_LIMITED:       { retryable: true,  suggested_actions: ["wait_and_retry"] },
    INTERNAL_ERROR:     { retryable: true,  suggested_actions: ["retry_with_backoff", "report_issue"] },
  };
  return {
    content: [{ type: "text" as const, text: JSON.stringify({ ...defaults[category], ...opts, error_category: category, message }) }],
    isError: true,
  };
}

// Usage:
return serfError("RATE_LIMITED", "GitHub API rate limit exceeded", {
  retry_after_ms: 60_000,
  suggested_actions: ["wait_60s_then_retry"],
});
```
