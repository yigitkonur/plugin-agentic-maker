# Derail scenarios for `/agentic-maker:build-cli`

Run from this folder (`target: ../..` is the plugin).

| Scenario | The worker is asked to | Receipts |
|---|---|---|
| `new` | build a small CLI from `docs/inventory-spec.md` for an agent caller | the spec's contract, checked by running the tool, plus `agentic-maker probe cli` on it |
| `repair` | make the seeded CLI (11 planted defects, see `fixtures/cli/seeded-cli/DEFECTS.md`) agent-friendly without running its `delete` | each defect fixed, the delete sentinel absent, `probe cli` clean |

`testdata/seeded-cli` is a copy of `fixtures/cli/seeded-cli/seeded-cli`; scenarios may only copy from inside their own project.
