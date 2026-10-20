# Config and Environment

> Read when: you are designing or auditing config precedence, profiles, multi-provider selection, or how a CLI detects CI, TTY and colour support.

Go code for effective-config, providers and environment detection is in `../frameworks/go/discovery-and-auth-config.md` and `../frameworks/go/discovery-and-auth-env.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Configuration Precedence | audit-agentic-cli/references/discovery-and-auth.md#Config Precedence (High → Low) -->
## Config precedence

Resolve each value from the highest-priority source that sets it:

| Priority | Source | Example |
|----------|--------|---------|
| 1 (highest) | CLI flags | `mycli --api-url https://custom.api.com deploy` |
| 2 | Environment variables | `MYCLI_API_URL=https://env.api.com mycli deploy` |
| 3 | Project config (`.mycli.yaml` in cwd or parents) | `api_url: https://project.api.com` |
| 4 | User config (`~/.config/mycli/config.yaml`) | `api_url: https://user.api.com` |
| 5 | System config (`/etc/mycli/config.yaml`) | `api_url: https://system.api.com` |
| 6 | Defaults (built into the binary) | `api_url: https://api.example.com` |

Credentials follow the same order without the system layer; see `auth-and-secrets.md`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Debug Config Sources | audit-agentic-cli/references/discovery-and-auth.md#5. Configuration Management | audit-agentic-cli/references/discovery-and-auth.md#Show Effective Config -->
## Show effective config

`mycli config show --effective --json` tells the agent where every value came from. The sources show two shapes. Per-value objects with the lookup trail:

```json
{
  "api_url": {
    "value": "https://custom.api.com",
    "source": "flag",
    "sources_checked": ["flag", "env", "project", "user", "system", "default"]
  },
  "timeout": {
    "value": "30s",
    "source": "user_config",
    "file": "~/.config/mycli/config.yaml"
  }
}
```

Or flat fields with a `_source` suffix:

```json
{
  "api_url": "https://api.example.com",
  "api_url_source": "environment_variable",
  "timeout": "30s",
  "timeout_source": "config_file",
  "profile": "production",
  "profile_source": "flag"
}
```

> Unresolved: the two shapes and their source labels (`flag`/`env`/`project`/`user`/`system`/`default` versus `environment_variable`/`config_file`) differ. Pick one shape and one label set per CLI and keep it stable; the per-value object with `source` and `sources_checked` carries more information.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Profile Support | audit-agentic-cli/references/discovery-and-auth.md#Config File Example -->
## Profiles

```bash
mycli --profile production deploy
# Uses [profiles.production] from config
```

```yaml
# ~/.config/mycli/config.yaml
api_url: https://api.example.com
timeout: 30s
output_format: json

profiles:
  production:
    api_url: https://api.prod.example.com
    timeout: 60s
  staging:
    api_url: https://api.staging.example.com
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#6. Multi-Provider Support | audit-agentic-cli/references/discovery-and-auth.md#Provider Selection | audit-agentic-cli/references/discovery-and-auth.md#Normalized Resource Schema -->
## Multi-provider support

Select the provider by flag or by config:

```bash
mycli --provider aws deploy
mycli --provider gcp deploy
```

```yaml
providers:
  default: aws
  aws:
    region: us-east-1
  gcp:
    project: my-project
```

Normalize every provider's resources into one schema and keep provider-only fields under `provider_data`:

```json
{
  "id": "res_123",
  "name": "my-resource",
  "provider": "aws",
  "region": "us-east-1",
  "status": "active",
  "provider_data": {
    "aws": {
      "arn": "arn:aws:..."
    }
  }
}
```

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#8. Environment Detection -->
## Environment detection

`mycli env --json` reports the runtime context:

```json
{
  "os": "linux",
  "arch": "amd64",
  "terminal": true,
  "ci": false,
  "ci_platform": null,
  "shell": "bash",
  "color_support": true
}
```

Detection rules from the reference implementation:

- Terminal: stdout is a character device.
- CI: any of `CI`, `GITHUB_ACTIONS`, `GITLAB_CI`, `JENKINS_URL`, `CIRCLECI`, `TRAVIS` is set. `ci_platform` is then `github_actions`, `gitlab`, `jenkins`, `circleci` or `travis`.
- Shell: the base name of `SHELL`, or `unknown`.
- Colour, in this order: `NO_COLOR` set means off; `FORCE_COLOR` set means on; CI or non-terminal means off; otherwise on only when `TERM` is non-empty and not `dumb`.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Auto-Adjust Behavior -->
## Auto-adjust behavior

- `CI=true`: disable colours, progress bars and prompts.
- `NO_COLOR=1`: disable colours.
- Non-TTY: disable prompts and spinners.

<!-- src: audit-agentic-cli/references/discovery-and-auth.md#Using Environment in Commands -->
## Using the environment in commands

Derive the output configuration once, at the start of the command:

| Setting | Rule |
|---------|------|
| JSON | `--json` flag, or stdout is not a terminal |
| Colour | colour supported and not JSON |
| Progress | terminal and not CI |
| Prompts | terminal, not CI, and not `--no-input` |

If prompts are off and the command needs input, fail instead of waiting: exit 2 naming the flag that would supply it (`--yes` to auto-confirm, or the missing required flags).

> Reconciled: the reference implementation returned a generic error here; this file uses exit 2 naming the flag, as in `discovery-and-help.md`.
