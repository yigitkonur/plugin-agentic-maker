# Derail scenarios for `/agentic-maker:build-mcp`

Run from this folder (`target: ../..` is the plugin).

| Scenario | The worker is asked to | Receipts |
|---|---|---|
| `add-a-tool` | add a reversible `suspend_user` tool to a clean server, consistent with its siblings | the tool exists with a flat schema and `destructiveHint: false`, the old tools and `delete_user`'s marking survive, `agentic-maker probe mcp` clean |
| `repair` | make the seeded server (planted defects: banner on stdout, duplicate and unnamed tools, undocumented tools, unmarked destructive tool, failure reported as success) usable | no stdout banner, every tool named and described, destructive tools marked, `probe mcp` clean |

`testdata/` holds copies of `fixtures/mcp/{_mini,clean-server,seeded-server}.py`; scenarios may only copy from inside their own project.
