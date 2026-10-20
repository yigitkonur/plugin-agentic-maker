---
max_turns: 6
allowed_tools: [Read, Glob, Grep, Skill]
---

My agent keeps failing to parse the output of our deploy CLI: it mixes progress text into the JSON and every error exits 1. How should I fix the CLI so an agent can use it?
