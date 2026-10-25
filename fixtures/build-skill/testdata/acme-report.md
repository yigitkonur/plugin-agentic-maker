# acme-report (internal CLI), facts verified 2026-10-20 against v3.2.0

`acme-report` prints and exports usage reports for the Acme billing system.

## Commands
- `acme-report list [--since YYYY-MM-DD] [--team NAME] [--json]` lists report ids, newest first. Default `--since` is 30 days ago.
- `acme-report show <report-id> [--json]` prints one report. Exit 3 if the id does not exist.
- `acme-report export <report-id> --format csv|json --out FILE` writes the report. Refuses to overwrite FILE unless `--force` is given (exit 4).
- `acme-report token --check` prints `ok` when ACME_TOKEN is valid, otherwise exits 7.

## Environment
- `ACME_TOKEN` (required, from the billing portal, valid 24 hours). Never pass it on the command line.
- `ACME_REGION` (optional): `eu` (default) or `us`.

## Exit codes
0 success, 2 usage error, 3 not found, 4 would overwrite, 7 auth failed or token expired.

## Gotchas
- `--since` older than 400 days is silently capped at 400 days.
- `export --format csv` writes semicolons as separators when ACME_REGION=eu.
