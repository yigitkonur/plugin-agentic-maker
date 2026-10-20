# Structural enforcement: dependency chains, guard params, workflow stages

> Read when: a multi-step or destructive MCP workflow needs ordering guaranteed by the server instead of by instructions.

<!-- src: audit-agentic-mcp/references/patterns/agentic-patterns.md#Agentic Patterns -->
Patterns for reliable multi-step agent workflows: structural enforcement, safe coordination and machine-readable errors. State-based `_available_actions` and the steering rules are in `../decisions/steering-contract.md`; bounded server-side continuation is in `patterns-bounded-continuation.md`; the error taxonomy and the shared event log are in `patterns-error-taxonomy-and-event-log.md`. Code (TypeScript): `../frameworks/mcp-ts/agentic-patterns.md`, `../frameworks/mcp-ts/agentic-patterns-stages.md`.

Enforcement ladder: documentation and prompt guidance are suggestions; schema dependencies, guard params and stage gates are enforcement. Choose by stakes.

<!-- src: audit-agentic-mcp/references/patterns/agentic-patterns.md#1. Parameter Dependency Chains -->
## Parameter dependency chains

Force the call order by requiring the output of an earlier tool as a mandatory input of a later one. The ordering becomes a structural constraint enforced by the schema, not just by documentation. Without it an agent may call `deploy_service` before `run_tests`; with it, the server rejects the call if the prerequisite token is absent.

Example: `run_tests(suite)` runs the suite; on failures it returns `isError: true` ("Tests failed: N failures"); on success it signs a token proving the tests passed (`{suite, passed: true, ts}` signed with a server secret) and returns "All N tests passed. test_token: ... Now call deploy_service with this test_token." Then `deploy_service(service_name, environment enum[staging, production], test_token "Token returned by run_tests. Required.")` verifies the token and, if invalid, returns "Invalid test_token. Run run_tests first."

Why it beats documentation: a description saying "call run_tests before deploy" relies on the model reading and following it. A required `test_token` parameter makes skipping structurally impossible; the call fails schema validation before the handler runs. Workflows that modify production need hard ordering guarantees, and structural dependency chains are the only reliable way to get them across all LLMs.

<!-- src: audit-agentic-mcp/references/patterns/agentic-patterns.md#3. Guard Tools: Precondition Validation via Boolean Params -->
## Guard params: precondition validation via boolean parameters

Add boolean precondition parameters to destructive tools. The agent must affirm the conditions before the server proceeds. Unlike confirmation dialogs (which only delay), guard params shift **responsibility**: the agent declares that preconditions were verified, and the server can validate the claim.

Example `delete_environment(environment_id, tests_verified, backup_confirmed, backup_id?)`:
- `tests_verified`: "Set true only after validate_environment returned no critical errors."
- `backup_confirmed`: "Set true only after create_backup returned a valid backup_id."
- `backup_id`: "The backup_id from create_backup. Required when backup_confirmed=true."

Blocking messages (`isError: true`): "Blocked: tests_verified is false. Run validate_environment first and confirm no critical errors."; "Blocked: backup_confirmed is false or backup_id is missing. Run create_backup first."; and, after an optional check that the backup exists, "Blocked: backup_id "..." not found or expired. Re-run create_backup."

Layered trust model:
- **Soft guard:** boolean params in the schema; the agent self-reports; the server accepts in good faith.
- **Medium guard:** the server checks a signed token or ID from a prerequisite tool (dependency chains above).
- **Hard guard:** the server independently re-runs the precondition check before executing.

Choose the layer by stakes: a destructive cloud operation warrants a hard guard; a local file operation may need only soft. Guard params make the agent acknowledge preconditions rather than rush, and they leave audit-log evidence of what the agent claimed before a destructive action.

<!-- src: audit-agentic-mcp/references/patterns/agentic-patterns.md#6. Server-Enforced Workflow Stages -->
## Server-enforced workflow stages

Keep a `WorkflowStage` enum on the server and reject tool calls that arrive out of sequence. This differs from prompt-based guidance (response text that *guides* the agent through stages, see `../decisions/steering-contract.md`): here the server *blocks* out-of-order calls, making the wrong path structurally impossible.

Stages in order: `initialized`, `data_loaded`, `analysis_complete`, `changes_validated`, `committed`. A stage-to-tool map names the tool that completes each stage: `initialized` -> `load_data`, `data_loaded` -> `analyze_data`, `analysis_complete` -> `validate_changes`, `changes_validated` -> `commit_changes`, `committed` -> "(workflow complete)". `commit_changes(session_id, dry_run=false)` asserts the current stage is `changes_validated`; otherwise it returns an error with `message` ("Stage gate: current stage is "X". Must complete "Y" before calling this tool."), `current_stage`, `required_stage` and `next_required_tool`. On success it records `committed`.

Without server-enforced stages agents routinely skip prerequisites (`deploy` before `validate`, `commit` before `analyze`) and nothing structurally stops them. For consequential workflows (deployments, financial operations, data migrations), server-side stage enforcement is the only reliable safeguard.

