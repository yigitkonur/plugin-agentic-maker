# Changing the tool list at runtime: unlocking, cache cost, notifications, fallbacks

> Read when: tools will be hidden, unlocked or removed during a session and you need to know when it is safe, how to signal it, and what a stale call should get back.

Companion to `patterns-progressive-discovery.md`. Code: `../frameworks/mcp-ts/progressive-discovery.md`, `../frameworks/mcp-python/progressive-discovery-fastmcp.md`. Provider-cache economics of tool-list changes: `budget-cache-stable-prefix.md`.

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#3. Session-Based Progressive Tool Unlocking -->
## Session-based progressive unlocking

Hide sensitive or advanced tools by default and reveal them only after authorization or a prerequisite action in the session. Example flow: mount the admin tools, disable them by tag by default, and add a gatekeeper tool `unlock_admin_mode` (requires the `super-user` OAuth scope) whose response lists the tools just made available.

How it works:
1. The agent initially sees only safe, read-only tools.
2. When a task needs admin capability it calls `unlock_admin_mode`.
3. The server verifies authorization and reveals the admin tools for this session only.
4. Other sessions are unaffected.

It solves three problems: **security** (destructive tools are invisible until authenticated), **context efficiency** (the initial list stays small), **progressive complexity** (users start simple and escalate). Building blocks in the source's framework: visibility transforms control components per session, auth middleware gates groups of components by tag, and session state tracks what each user unlocked (version note and API: `../frameworks/mcp-python/progressive-discovery-fastmcp.md`).

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#5. Dynamic Tool List Changes Nuke the KV/Prefix Cache -->
## Tool-list changes invalidate the prefix cache

Changing the tool list invalidates the KV/prefix cache at the major providers: the system prompt, which includes tool definitions, is cached as a prefix, so every add/remove evicts the entry and forces recomputation. Dynamic pruning can be slower than a static list when tools change too often.

Change tools only at clear session boundaries:
- After an explicit `init_mode` or `set_context` call from the user.
- When moving between workflow phases (for example "explore" to "edit").
- On initial connection setup.

Do not change the list on every request or from per-message heuristics.

Rule of thumb:

```
If tool_list_change_frequency > 1 per ~20 requests: you're probably hurting more than helping.
If tool_list is stable for the session: prefix cache stays warm -> faster time-to-first-token, lower cost.
```

Good: change tools once on a mode switch (one invalidation). Bad: prune "irrelevant" tools on every `tools/call` (cache miss every time). Static lists are cache-friendly; batch mutations at session boundaries.

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#6. Use `notifications/tools/list_changed` for Dynamic Tooling -->
## Signal changes with notifications/tools/list_changed

When the server adds, removes or modifies tools at runtime, emit `notifications/tools/list_changed`, the official MCP mechanism. The client re-fetches `tools/list` and sees the new set; without it clients use stale definitions, calling removed tools or missing new ones.

SDK support: the TypeScript SDK's registered-tool handle sends the notification automatically on each mutation: `disable()` (hide), `enable()` (show again), `update({description: ...})`, `remove()` (permanent). A manual notification with method `notifications/tools/list_changed` is also possible (code and version note: `../frameworks/mcp-ts/progressive-discovery.md`).

Send it at session boundaries (previous section) to avoid prefix-cache thrashing: the notification is cheap, the cache invalidation it triggers on the LLM side is not.

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#7. FastMCP Visibility Transforms -->
## Session-scoped visibility (FastMCP)

Session-level visibility lets you show or hide tools without re-registering anything, the production way to do progressive disclosure in Python servers: disable by tag or by name globally, enable per session from inside a gatekeeper tool, with the layer order global transforms -> session transforms -> tool-level annotations (later layers override earlier ones). Without it you must re-register tools (which invalidates the prefix cache) or run a server instance per user tier. Snippets: `../frameworks/mcp-python/progressive-discovery-fastmcp.md`.

<!-- src: audit-agentic-mcp/references/patterns/progressive-discovery.md#8. Graceful Fallback for Hidden Tools -->
## Graceful fallback for hidden tools

A stateful model may remember a hidden tool from earlier and call it. Do not answer with a generic not-found error.

Detection and recovery:
- Keep a registry of all tools (including currently hidden ones) and a set of visible ones.
- On a call to an unknown name, check the registry. If the tool exists but is hidden, return `isError: true` with an error `TOOL_NOT_CURRENTLY_VISIBLE`, the `tool_name`, a message ("exists but is not active in your current session mode"), `how_to_unlock` ("Call {unlockVia} first to activate this tool." or "Contact your administrator to enable this capability.") and `current_alternatives` (for example "Call search_tools to discover available alternatives").
- If the tool is truly unknown, return `Unknown tool: "{name}". Call list_tools to see available tools.`

On-demand restoration: a `restore_tool(tool_name, reason)` tool ("Restore a temporarily hidden tool for this session") errors if the name does not exist, otherwise adds it to the visible set, sends the tools-changed notification and confirms.

Without a graceful fallback a model that remembers a hidden tool retries it repeatedly, wasting context on uninformative errors; `TOOL_NOT_CURRENTLY_VISIBLE` guides recovery.
