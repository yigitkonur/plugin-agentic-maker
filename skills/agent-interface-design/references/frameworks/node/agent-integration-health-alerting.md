# Node/TypeScript: Health Checks and Alerting for CLI Calls

> Read when: you need TypeScript code that probes a CLI's health and raises webhook alerts on error rate or p99 latency.

The rules, thresholds and probe commands are in `../../cli/caller-observability.md`. These snippets reuse `invokeCLI` from `agent-integration.md`.

## Health checks

```typescript
interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  checks: Record<string, {
    status: 'pass' | 'fail';
    latency_ms?: number;
    message?: string;
  }>;
  timestamp: string;
}

async function checkCLIHealth(): Promise<HealthStatus> {
  const checks: HealthStatus['checks'] = {};

  // invokeCLI never rejects: a failure comes back as ok: false
  const probe = async (cmd: string[], failMessage: string): Promise<HealthStatus['checks'][string]> => {
    const start = Date.now();
    const result = await invokeCLI(cmd, { timeout: 5000 });
    return { status: result.ok ? 'pass' : 'fail', latency_ms: Date.now() - start, ...(result.ok ? {} : { message: failMessage }) };
  };
  checks.cli_accessible = await probe(['mycli', 'version', '--json'], 'CLI not accessible');
  checks.daemon_running = await probe(['mycli', 'daemon', 'status', '--json'], 'Daemon not responding');
  checks.auth_valid = await probe(['mycli', 'account', 'whoami', '--json'], 'Auth check failed');

  // Determine overall status
  const failedChecks = Object.values(checks).filter((c) => c.status === 'fail').length;
  let status: HealthStatus['status'] = 'healthy';
  if (failedChecks > 0) status = 'degraded';
  if (failedChecks === Object.keys(checks).length) status = 'unhealthy';

  return {
    status,
    checks,
    timestamp: new Date().toISOString(),
  };
}
```

## Alerting integration

```typescript
interface AlertConfig {
  webhook_url: string;
  threshold_errors_per_minute: number;
  threshold_latency_p99_ms: number;
}

class AlertManager {
  private errors: number[] = [];
  private latencies: { t: number; ms: number }[] = [];
  private readonly windowMs = 60000;

  constructor(private config: AlertConfig) {}

  recordInvocation(ok: boolean, latencyMs: number): void {
    const now = Date.now();

    // Clean old entries
    this.errors = this.errors.filter((t) => now - t < this.windowMs);
    this.latencies = this.latencies.filter((l) => now - l.t < this.windowMs);

    if (!ok) this.errors.push(now);
    this.latencies.push({ t: now, ms: latencyMs });

    this.checkThresholds();
  }

  private checkThresholds(): void {
    // Check error rate
    if (this.errors.length > this.config.threshold_errors_per_minute) {
      this.sendAlert('error_rate', {
        errors_per_minute: this.errors.length,
        threshold: this.config.threshold_errors_per_minute,
      });
    }

    // Check p99 latency
    if (this.latencies.length >= 10) {
      const sorted = this.latencies.map((l) => l.ms).sort((a, b) => a - b);
      const p99 = sorted[Math.floor(sorted.length * 0.99)];
      if (p99 > this.config.threshold_latency_p99_ms) {
        this.sendAlert('high_latency', {
          p99_latency_ms: p99,
          threshold: this.config.threshold_latency_p99_ms,
        });
      }
    }
  }

  private lastAlert: Record<string, number> = {};

  private sendAlert(type: string, data: Record<string, unknown>): void {
    const now = Date.now();
    if (now - (this.lastAlert[type] ?? 0) < this.windowMs) return; // one alert per type per window
    this.lastAlert[type] = now;
    fetch(this.config.webhook_url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        alert_type: type,
        timestamp: new Date().toISOString(),
        data,
      }),
    }).catch((err) => console.error('Alert webhook failed:', (err as Error).message)); // never an unhandled rejection
  }
}
```

> Note: the source stored latencies as bare numbers and filtered them with `now - t < windowMs`, comparing a latency to a timestamp, so entries never expired. This file stores `{ t, ms }` pairs and filters on `t` before computing p99.
