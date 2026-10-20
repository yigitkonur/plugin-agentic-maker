# Scoring an audit

> Read when: you finish an audit and must turn the findings into a scorecard.

The score summarizes the findings; it measures nothing by itself. The findings, each with its evidence, are the product. Read a score as "how much did the probes and the reading find", never as a grade.

## Per finding

| Severity | Meaning for an agent | Points off |
|---|---|---|
| Critical | the agent cannot continue or loses data (a hang, a command that deletes on a typo, a leaked secret) | 25 |
| High | the agent will misparse, misread or take the wrong action (stdout not JSON, silent success on a typo, a secret on argv) | 12 |
| Medium | the agent loses time or guesses (no examples, every failure exits 1, a description that overlaps another) | 5 |
| Low | friction with a cheap fix (no `--version`) | 2 |

## Per dimension and overall

Group the findings under the eight questions of the contract (intent, contract, discovery, steering, safety, budget, recovery, verification). A dimension starts at 100 and loses the points of its findings, with a floor of 0. The overall score is the lowest *measured* dimension rounded down to the nearest 5, **not** the average: a surface that is perfect except that it hangs is not 90 percent ready. Write how many of the eight dimensions were measured next to the overall ("75, 5 of 8 measured").

| Overall | Reading |
|---|---|
| 90-100 | an agent can drive it unattended; remaining findings are polish |
| 70-85 | usable with supervision; fix the High findings first |
| 50-65 | an agent will fail often; fix Critical and High before anything else |
| below 50 | not agent-ready |

## Which finding goes under which dimension

Probe findings carry a `check` field; file each under the dimension below. Findings you add by reading go under the dimension of the contract question they fail.

| `check` (CLI probe) | `check` (MCP probe) | Dimension |
|---|---|---|
| (read the surface) | `intent` | 1 Intent |
| `output`, `exit_codes` | `contract` | 2 Contract |
| `help`, `version` | `discovery` | 3 Discovery |
| (read the responses) | (read the responses) | 4 Steering: `not measured` unless you read for it |
| `safety`, `security` | `safety` | 5 Safety |
| (output size is not probed for CLIs) | `budget` | 6 Budget |
| `errors` | `errors` | 7 Recovery |
| `non_interactive` (a hang) | (a timed-out call) | 8 Verification |

## Rules

- A dimension that was **not measured** (a command was never run, a server was not connected) is reported as `not measured`, not as 100, and is left out of the overall.
- Do not mix scores from audits that ran different probes. Record which probes ran (`executed` in the probe result) next to the score.
- Illustrative audits quoted elsewhere in the references (for gh, kubectl, aws and similar) predate this rubric and are labelled illustrative; they are not comparable with a score from this one.
- After a fix, rerun the same probe and the same commands; compare findings, not scores.
