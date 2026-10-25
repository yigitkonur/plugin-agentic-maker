---
name: lint-js
description: Lint JavaScript and TypeScript files before a commit.
---

# Lint JavaScript

Run `npx eslint --max-warnings 0 .` from the project root. Fix what it reports; `npx eslint --fix .` handles formatting-only findings.
A non-zero exit means findings remain. Do not commit until the exit code is 0.
