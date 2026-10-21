# Roots and completions: honor workspace roots, narrow suggestions

> Read when: your server reads or writes files and today takes a `--dir` flag, or your resource templates and prompts have enum-like arguments users type by hand.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 6: Honor `roots/list` Instead Of Hard-Coding Workspace Paths -->
## Scope file access to roots/list

Rule: on session start, and on every `notifications/roots/list_changed`, call `roots/list` and scope all filesystem access to the returned `file://` URIs. Validate every path with `os.path.realpath` plus a prefix check to block symlink traversal. Fall back to CLI args or the current working directory only when the client does not advertise the `roots` capability (`roots.listChanged` is an optional sub-flag: without it, call `roots/list` once per session).

The spec mandates "validate all root URIs to prevent path traversal". Servers that take `--dir=` flags and ignore roots break whenever the user opens a new folder mid-session, because the server keeps indexing the old one. Roots are `file://` only: reject `http://`, `s3://` and other schemes per spec.

Check shape: keep only `file://` roots, resolve each with `realpath`, and accept a path only if its real path equals a root or starts with `root + separator`. Code: `../frameworks/mcp-python/advanced-protocol-roots-and-completion.md`.

When to use: any server that reads or writes files (filesystem, code search, git, build tools).

When NOT to use: the client does not support roots. Provide an explicit `workspace_path` tool argument instead.

> Note: the client support matrix and the list of clients without roots support are in `../fresh/mcp-advanced-feature-support.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 7: Implement `completion/complete` With Context-Aware Narrowing -->
## Implement completion/complete with context narrowing

Rule: if the server exposes resource templates or prompts with argument slots, implement `completion/complete`. Use the `context.arguments` field to narrow suggestions based on previously selected arguments. Cap each response at 100 values and set `hasMore: true` plus `total` when truncating.

Completions are the MCP equivalent of shell tab-completion. Without them users type freeform values from a known finite set; a wrong value makes the tool fail and the model retries blindly. Context narrowing closes a usability gap: when the user picks `language=python`, the `framework` completions return Django, Flask and FastAPI, not Rails.

Response shape: `{"values": [...up to 100], "total": N, "hasMore": bool}`; an unknown reference returns `{"values": []}`. Filter by prefix match on the typed value. Code: `../frameworks/mcp-python/advanced-protocol-roots-and-completion.md`. Revision that added `context.arguments`: `../fresh/mcp-advanced-feature-revisions.md`.

When to use: resource templates with parameters, prompts with enum-like arguments, dynamic lists (projects, models, repos) fetched live. See `protocol-resources.md` and `protocol-prompts.md`.

When NOT to use: arguments that are fully freeform text (user queries, messages), or when you cannot count on the client calling `completion/complete` (the server declares the `completions` capability; client support was uneven at the survey date).
