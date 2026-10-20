---
name: manifest-synth
description: Synthesizes semver-delimited artefact manifests from VCS delta enumerations for downstream distribution channels.
---

# Manifest synthesis

Turn a plain list of commits into release notes.

1. Run the grouping helper on the commit list: `python3 scripts/group.py commits.txt`.
2. Write `RELEASE_NOTES.md` in the format described in `reference/format.md`.
3. Keep each entry short.
