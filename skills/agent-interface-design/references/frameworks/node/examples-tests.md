# Node/TypeScript: Testing JSON Output

> Read when: you need Vitest tests that spawn the CLI and check exit code and envelope fields.

<!-- src: audit-agentic-cli/references/examples.md#16.3 Unit Testing JSON Output (Node.js) -->
## Unit testing JSON output

```typescript
import { spawn } from 'child_process';
import { describe, it, expect } from 'vitest';

interface CLIResult {
  exitCode: number;
  stdout: string;
  stderr: string;
  json: any;
}

async function runCLI(...args: string[]): Promise<CLIResult> {
  return new Promise((resolve) => {
    const proc = spawn('./mycli', [...args, '--json']);
    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => { stdout += data; });
    proc.stderr.on('data', (data) => { stderr += data; });

    proc.on('close', (exitCode) => {
      let json: any;
      try {
        json = JSON.parse(stdout); // the envelope is always on stdout
      } catch {
        json = { raw: stdout, stderr };
      }
      resolve({ exitCode: exitCode ?? 1, stdout, stderr, json });
    });
  });
}

describe('CLI JSON Output', () => {
  it('returns success envelope on create', async () => {
    const result = await runCLI('create', 'test-resource');

    expect(result.exitCode).toBe(0);
    expect(result.json.ok).toBe(true);
    expect(result.json.result).toBeDefined();
    expect(result.json.result.created).toBe(true);
  });

  it('returns not_found error with exit code 3', async () => {
    const result = await runCLI('get', 'nonexistent');

    expect(result.exitCode).toBe(3);
    expect(result.json.ok).toBe(false);
    expect(result.json.error.class).toBe('not_found');
    expect(result.json.error.code).toBe('RESOURCE_NOT_FOUND');
    expect(result.json.error.retryable).toBe(false);
  });

  it('returns usage error when confirmation missing', async () => {
    const result = await runCLI('delete', 'res_123');

    expect(result.exitCode).toBe(2);
    expect(result.json.ok).toBe(false);
    expect(result.json.error.class).toBe('usage');
  });

  it('--dry-run returns preview without executing', async () => {
    const result = await runCLI('create', 'test', '--dry-run');

    expect(result.exitCode).toBe(0);
    expect(result.json.ok).toBe(true);
    expect(result.json.result.dry_run).toBe(true);
  });

  describe('standard flags', () => {
    const flags = [
      { long: '--quiet', short: '-q' },
      { long: '--yes', short: '-y' },
      { long: '--force', short: '-f' },
    ];

    for (const { long, short } of flags) {
      it(`${short} is alias for ${long}`, async () => {
        const r1 = await runCLI('list', long);
        const r2 = await runCLI('list', short);

        expect(r1.json.ok).toBe(r2.json.ok);
      });
    }
  });
});
```

> Reconciled: the source parsed `stdout || stderr`; the envelope is always on stdout, so this test parses stdout only.
