# Node.js: Interactive Detection, Prompt and Confirm

> Read when: you are implementing TTY-aware prompt and confirm helpers in a Node.js / TypeScript CLI.

## Interactive detection, prompt and confirm

Contract: `../../cli/non-interactive.md`.

> Reconciled: the source `confirm` returned `false` when non-interactive. Here a confirmation that cannot be asked fails with exit 2 naming `--yes` / `--force`, and prompts go to stderr.

```typescript
import * as readline from 'readline';

function isInteractive(): boolean {
  if (process.env.MYCLI_NON_INTERACTIVE) {
    return false;
  }
  return process.stdin.isTTY && process.stdout.isTTY;
}

async function prompt(
  message: string,
  options: { nonInteractive?: boolean } = {}
): Promise<string> {
  if (options.nonInteractive || !isInteractive()) {
    throw new Error(`Prompt required in non-interactive mode: ${message}`);
  }

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stderr, // prompts go to stderr
  });

  return new Promise((resolve, reject) => {
    let answered = false;
    rl.on('SIGINT', () => { rl.close(); process.exit(130); }); // Ctrl-C at the prompt is a signal exit
    rl.on('close', () => { if (!answered) reject(new Error('Input ended before an answer')); });
    rl.question(message, (answer) => {
      answered = true;
      rl.close();
      resolve(answer);
    });
  });
}

async function confirm(
  message: string,
  options: { nonInteractive?: boolean; autoYes?: boolean } = {}
): Promise<boolean> {
  if (options.autoYes) {
    return true;
  }

  if (options.nonInteractive || !isInteractive()) {
    console.error(`Confirmation required: ${message}. Re-run with --yes or --force.`);
    process.exit(2);
  }

  const answer = await prompt(`${message} [y/N]: `);
  return answer.toLowerCase() === 'y';
}
```
