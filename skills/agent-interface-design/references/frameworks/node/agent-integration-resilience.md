# Node/TypeScript: Auth Refresh, Conflict Resolution, Circuit Breaker, Fallback

> Read when: you need TypeScript code for recovering from exit 4 and exit 5, breaking the circuit on repeated failures, or falling back to cached data.

The rules and thresholds are in `../../cli/caller-resilience.md`. These snippets reuse `CLIResult`, `CLIAgent` and `invokeCLI` from `agent-integration.md`.

## Auth token refresh

```typescript
interface TokenManager {
  getToken(): Promise<string>;
  refreshToken(): Promise<string>;
  clearToken(): void;
}

class AuthRecoveryCLI {
  constructor(
    private cli: CLIAgent,
    private tokens: TokenManager
  ) {}

  async invokeWithAuthRecovery(cmd: string[]): Promise<CLIResult> {
    let result = await this.cli.invoke(cmd);

    // Exit code 4 = auth error
    if (!result.ok && result.exit_code === 4) {
      console.warn('Auth expired, refreshing token...');

      try {
        await this.tokens.refreshToken();
        // Retry with fresh token
        result = await this.cli.invoke(cmd);
      } catch (refreshError) {
        // Refresh failed, force re-login
        this.tokens.clearToken();
        await this.cli.invoke(['auth', 'login', '--yes']);
        result = await this.cli.invoke(cmd);
      }
    }

    return result;
  }
}
```

## Conflict resolution

```typescript
type ConflictStrategy = 'force' | 'merge' | 'abort' | 'prompt';

async function invokeWithConflictResolution(
  cmd: string[],
  strategy: ConflictStrategy = 'merge'
): Promise<CLIResult> {
  const result = await invokeCLI(cmd);

  // Exit code 5 = conflict
  if (!result.ok && result.exit_code === 5) {
    const conflictData = (result.error?.details ?? {}) as { base_version?: string; current_version?: string };

    switch (strategy) {
      case 'force':
        // Retry with --force flag
        return invokeCLI([...cmd, '--force']);

      case 'merge':
        // Attempt three-way merge
        const mergeCmd: string[] = [
          'mycli', 'resource', 'merge',
          '--base', conflictData.base_version ?? '',
          '--current', conflictData.current_version ?? '',
          '--json', '--yes'
        ];
        const mergeResult = await invokeCLI(mergeCmd);
        if (mergeResult.ok) {
          return invokeCLI(cmd); // Retry original
        }
        return mergeResult;

      case 'abort':
        return result; // Return conflict as-is

      case 'prompt':
        // In agent context, escalate to human
        return {
          ok: false,
          error: {
            ...result.error!, // keep the conflict class and code
            message: `Conflict requires human resolution: ${result.error!.message}`,
            retryable: false,
          },
          exit_code: 5,
        };
    }
  }

  return result;
}
```

## Circuit breaker

```typescript
enum CircuitState {
  CLOSED = 'closed',    // Normal operation
  OPEN = 'open',        // Failing fast
  HALF_OPEN = 'half_open', // Testing recovery
}

class CircuitBreaker {
  private state = CircuitState.CLOSED;
  private failures = 0;
  private lastFailure = 0;
  private readonly threshold: number;
  private readonly resetTimeout: number;

  constructor(options: { threshold?: number; resetTimeoutMs?: number } = {}) {
    this.threshold = options.threshold ?? 5;
    this.resetTimeout = options.resetTimeoutMs ?? 60000;
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === CircuitState.OPEN) {
      if (Date.now() - this.lastFailure > this.resetTimeout) {
        this.state = CircuitState.HALF_OPEN;
      } else {
        throw new Error('Circuit breaker is OPEN - failing fast');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = CircuitState.CLOSED;
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.threshold) {
      this.state = CircuitState.OPEN;
    }
  }

  getState(): CircuitState {
    return this.state;
  }
}

// Usage with CLI
const breaker = new CircuitBreaker({ threshold: 3, resetTimeoutMs: 30000 });

class BreakerFailure extends Error {
  constructor(public result: CLIResult) { super(result.error?.message); }
}

async function resilientInvoke(cmd: string[]): Promise<CLIResult> {
  try {
    return await breaker.execute(async () => {
      const result = await invokeCLI(cmd);
      // only outages (transient 7 incl. timeouts, crash 1) trip the breaker; usage, auth, conflict do not
      if (!result.ok && (result.exit_code === 7 || result.exit_code === 1)) {
        throw new BreakerFailure(result);
      }
      return result;
    });
  } catch (error) {
    if (error instanceof BreakerFailure) return error.result;
    return { ok: false, error: { class: 'dependency_failed', code: 'CIRCUIT_OPEN', message: (error as Error).message, retryable: true }, exit_code: 7 };
  }
}
```

## Graceful degradation

```typescript
interface FallbackOptions {
  primary: () => Promise<CLIResult>;
  fallback: () => Promise<CLIResult>;
  shouldFallback: (result: CLIResult) => boolean;
}

async function withFallback(options: FallbackOptions): Promise<CLIResult> {
  const primaryResult = await options.primary();

  if (options.shouldFallback(primaryResult)) {
    console.warn('Primary failed, attempting fallback...');
    return options.fallback();
  }

  return primaryResult;
}

// Example: Fall back to cached data on API failure
const result = await withFallback({
  primary: () => invokeCLI(['mycli', 'resource', 'get', 'id', '--json']),
  fallback: () => invokeCLI(['mycli', 'cache', 'get', 'id', '--json']),
  shouldFallback: (r) => !r.ok && r.exit_code === 7, // Transient error
});
```
