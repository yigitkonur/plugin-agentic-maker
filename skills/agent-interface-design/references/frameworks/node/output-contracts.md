# Node.js: Schema Validation, Exit Codes, JSONL Emitters, Complete Example

> Read when: you are implementing or consuming the output contract of a Node.js / TypeScript CLI (Ajv validation, exit constants, emitters, stdout/stderr split).

<!-- src: audit-agentic-cli/references/output-contracts.md#Schema Validation Example -->
## Schema validation with Ajv

Validates a CLI's stdout against the schemas in `../../cli/envelope-schemas.md`.

```typescript
import Ajv from 'ajv';
import successSchema from './schemas/success-response.json';
import errorSchema from './schemas/error-response.json';

const ajv = new Ajv({ allErrors: true });
const validateSuccess = ajv.compile(successSchema);
const validateError = ajv.compile(errorSchema);

type SuccessResponse = { ok: true; command: string; schema_version: string; result: unknown; meta: object };
type ErrorResponse = { ok: false; error: { class: string; code: string; message: string; retryable: boolean; suggestion?: string } };

function parseCliOutput(stdout: string): SuccessResponse | ErrorResponse {
  const data = JSON.parse(stdout);

  if (data.ok === true) {
    if (!validateSuccess(data)) {
      throw new Error(`Invalid success response: ${ajv.errorsText(validateSuccess.errors)}`);
    }
    return data as SuccessResponse;
  } else {
    if (!validateError(data)) {
      throw new Error(`Invalid error response: ${ajv.errorsText(validateError.errors)}`);
    }
    return data as ErrorResponse;
  }
}
```

## Exit code constants

The table they implement is `../../cli/exit-codes.md`.

```typescript
// exitcodes.ts
export const ExitCode = {
  SUCCESS: 0,     // Operation completed successfully
  CRASH: 1,       // Unexpected error, internal failure
  USAGE: 2,       // Bad flags, invalid arguments
  NOT_FOUND: 3,   // Resource does not exist
  AUTH: 4,        // Authentication/authorization failed
  CONFLICT: 5,    // Resource conflict (exists, version mismatch)
  VALIDATION: 6,  // Input validation failed
  TRANSIENT: 7,   // Retryable error (network, timeout, rate limit)
  PARTIAL: 8,     // Partial success (some operations failed)
} as const;

export type ExitCodeValue = typeof ExitCode[keyof typeof ExitCode];
```

## JSONL emitters

> Note: progress events go to stderr (`console.error`); the terminal result goes to stdout (`../../cli/streams-and-jsonl.md`).

```typescript
interface ProgressEvent {
  type: 'progress';
  phase: string;
  percent?: number;
  message?: string;
  timestamp: string;
}

interface CompletedEvent {
  type: 'completed';
  status: string;
  result: unknown;
}

function emitProgress(phase: string, percent?: number, message?: string): void {
  const event: ProgressEvent = {
    type: 'progress',
    phase,
    percent,
    message,
    timestamp: new Date().toISOString(),
  };
  console.error(JSON.stringify(event));
}

function emitCompleted(result: unknown): void {
  const event: CompletedEvent = {
    type: 'completed',
    status: 'succeeded',
    result,
  };
  console.log(JSON.stringify(event));
}
```

## Complete example

```typescript
import { exit } from 'process';
import { ExitCode } from './exitcodes';

async function main() {
  // Progress to stderr
  console.error('Connecting to server...');

  try {
    const result = await doOperation();

    // Success JSON to stdout
    console.log(JSON.stringify({
      ok: true,
      command: 'mycli op',
      schema_version: '1.0',
      result,
      meta: {},
    }));
    exit(ExitCode.SUCCESS);

  } catch (error) {
    // Error JSON to stdout
    console.log(JSON.stringify({
      ok: false,
      error: {
        class: 'network',
        code: 'CONNECTION_FAILED',
        message: (error as Error).message,
        retryable: true,
        suggestion: 'Retry with backoff',
      },
    }));
    exit(ExitCode.TRANSIENT);
  }
}

main();
```
