# Node/TypeScript: Non-Interactive Mode and Commander Help

> Read when: you need TypeScript code for a confirmation that fails with exit 2 when there is no TTY, or for Commander help text with examples and a JSON help command.

Rules: `../../cli/discovery-and-help.md`, `../../cli/config-and-env.md`. Tests: `examples-tests.md`.

<!-- src: audit-agentic-cli/references/examples.md#3. Non-Interactive Mode (Node.js) -->
## Non-interactive mode

```typescript
import * as readline from 'readline';
import * as tty from 'tty';

interface CLIOptions {
  json: boolean;        // --json
  quiet: boolean;       // --quiet, -q
  yes: boolean;         // --yes, -y
  force: boolean;       // --force, -f
  dryRun: boolean;      // --dry-run
  timeout: string;      // --timeout
  nonInteractive: boolean;
}

function isInteractive(): boolean {
  return tty.isatty(process.stdin.fd) &&
         !process.env.CI &&
         !process.env.MYCLI_NON_INTERACTIVE;
}

async function confirm(message: string, opts: CLIOptions): Promise<boolean> {
  // Auto-yes mode
  if (opts.yes) return true;

  // Non-interactive: fail if we need confirmation
  if (opts.nonInteractive || !isInteractive()) {
    console.error(`Error: confirmation required but running non-interactively`);
    console.error(`Use --yes/-y to auto-confirm or --force/-f to bypass`);
    process.exit(2);
  }

  // Interactive prompt
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stderr
  });

  return new Promise((resolve) => {
    let answered = false;
    rl.on('SIGINT', () => { rl.close(); process.exit(130); }); // Ctrl-C at the prompt is a signal exit
    rl.on('close', () => { if (!answered) process.exit(2); }); // input ended with no answer: cannot ask
    rl.question(`${message} [y/N]: `, (answer) => {
      answered = true;
      rl.close();
      resolve(answer.toLowerCase() === 'y');
    });
  });
}
```

<!-- src: audit-agentic-cli/references/examples.md#8. Help Generation (Node.js with Commander) -->
## Help generation with Commander

```typescript
import { Command } from 'commander';

const program = new Command();

program
  .name('mycli')
  .description('Agent-friendly CLI tool')
  .version('1.0.0');

program
  .command('deploy <service>')
  .description('Deploy a service to the target environment')
  .requiredOption('--env <environment>', 'Target environment: dev, staging, prod')
  .option('--image <image>', 'Container image override')
  .option('--replicas <n>', 'Number of replicas', parseInt)
  .option('--dry-run', 'Preview changes without applying')
  .option('--wait', 'Wait for deployment to complete', true)
  .option('--timeout <duration>', 'Maximum wait time', '5m')
  .option('--json', 'Output result as JSON')
  .addHelpText('after', `
Examples:
  $ mycli deploy web-api --env staging
  $ mycli deploy web-api --env prod --image myregistry/web:v2.1.0 --json
  $ mycli deploy web-api --env dev --dry-run
`)
  .action(async (service, options) => {
    // Implementation
  });

// JSON help output (custom)
program
  .command('help-json')
  .description('Output help as JSON')
  .action(() => {
    const commands = program.commands.map(cmd => ({
      name: cmd.name(),
      description: cmd.description(),
      options: cmd.options.map(opt => ({
        flags: opt.flags,
        description: opt.description,
        required: opt.required,
        default: opt.defaultValue
      }))
    }));
    console.log(JSON.stringify({ commands }, null, 2));
  });

program.parse();
```

The machine-readable help here is a `help-json` command; the rule text calls it `mycli help --json`. Pick one spelling and document it.
