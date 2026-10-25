---
name: lint-py
description: Lint Python files before a commit.
---

# Lint Python

Run `ruff check .` and then `ruff format --check .` from the project root. `ruff check --fix .` handles the fixable findings.
A non-zero exit from either means findings remain. Do not commit until both exit 0.
