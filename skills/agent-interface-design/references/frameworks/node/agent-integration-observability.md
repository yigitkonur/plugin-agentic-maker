# Node/TypeScript: Logging, Metrics and Tracing for CLI Calls

> Read when: you need TypeScript code that logs, counts, times and traces each CLI invocation.

The rules, field lists and metric names are in `../../cli/caller-observability.md`. These snippets reuse `CLIResult` and `invokeCLI` from `agent-integration.md`.

## Structured logging

```typescript
import pino from 'pino';

const logger = pino({
  level: process.env.LOG_LEVEL || 'info',
  formatters: {
    level: (label) => ({ level: label }),
  },
});

interface InvocationLog {
  cmd: string[];
  duration_ms: number;
  exit_code?: number;
  ok: boolean;
  error_code?: string;
}

async function invokeCLIWithLogging(cmd: string[]): Promise<CLIResult> {
  const start = Date.now();
  const childLogger = logger.child({ cmd: cmd.join(' ') });

  childLogger.debug('CLI invocation starting');

  try {
    const result = await invokeCLI(cmd);
    const duration = Date.now() - start;

    const logData: InvocationLog = {
      cmd,
      duration_ms: duration,
      ok: result.ok,
      error_code: result.error?.code,
    };

    if (result.ok) {
      childLogger.info(logData, 'CLI invocation succeeded');
    } else {
      childLogger.warn(logData, 'CLI invocation failed');
    }

    return result;
  } catch (error) {
    childLogger.error({ err: error, duration_ms: Date.now() - start }, 'CLI invocation error');
    throw error;
  }
}
```

## Metrics collection

```typescript
import { Counter, Histogram, Registry } from 'prom-client';

const registry = new Registry();

const cliInvocations = new Counter({
  name: 'cli_invocations_total',
  help: 'Total CLI invocations',
  labelNames: ['command', 'status', 'exit_code'],
  registers: [registry],
});

const cliDuration = new Histogram({
  name: 'cli_duration_seconds',
  help: 'CLI invocation duration',
  labelNames: ['command'],
  buckets: [0.1, 0.5, 1, 2, 5, 10, 30, 60],
  registers: [registry],
});

const cliRetries = new Counter({
  name: 'cli_retries_total',
  help: 'CLI retry attempts',
  labelNames: ['command', 'reason'],
  registers: [registry],
});

async function invokeCLIWithMetrics(cmd: string[]): Promise<CLIResult> {
  const command = cmd.slice(0, 3).join('_'); // e.g., mycli_task_start
  const timer = cliDuration.startTimer({ command });

  try {
    const result = await invokeCLI(cmd);

    cliInvocations.inc({
      command,
      status: result.ok ? 'success' : 'failure',
      exit_code: result.error?.code || '0',
    });

    return result;
  } finally {
    timer();
  }
}

// Expose metrics endpoint
import express from 'express';
const app = express();
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', registry.contentType);
  res.end(await registry.metrics());
});
```

## Distributed tracing (OpenTelemetry)

```typescript
import { trace, SpanStatusCode, context } from '@opentelemetry/api';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

// Initialize tracer
const provider = new NodeTracerProvider();
provider.addSpanProcessor(new SimpleSpanProcessor(new OTLPTraceExporter()));
provider.register();

const tracer = trace.getTracer('cli-agent');

async function invokeCLIWithTracing(cmd: string[]): Promise<CLIResult> {
  return tracer.startActiveSpan('cli.invoke', async (span) => {
    span.setAttributes({
      'cli.command': cmd[0],
      'cli.subcommand': cmd.slice(1, 3).join(' '),
      'cli.args_count': cmd.length,
    });

    try {
      const result = await invokeCLI(cmd);

      span.setAttributes({
        'cli.ok': result.ok,
        'cli.error_code': result.error?.code || '',
      });

      if (!result.ok) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: result.error?.message,
        });
      }

      return result;
    } catch (error) {
      span.recordException(error as Error);
      span.setStatus({ code: SpanStatusCode.ERROR });
      throw error;
    } finally {
      span.end();
    }
  });
}

// Propagate trace context to CLI (if supported)
async function invokeCLIWithContextPropagation(cmd: string[]): Promise<CLIResult> {
  return tracer.startActiveSpan('cli.invoke', async (span) => {
    const traceId = span.spanContext().traceId;
    const spanId = span.spanContext().spanId;

    // Add trace context as env vars or headers
    const result = await invokeCLI(cmd, {
      env: {
        TRACE_ID: traceId,
        SPAN_ID: spanId,
      },
    });

    span.end();
    return result;
  });
}
```

> Note: the source's context-propagation example never ended its span; this file adds `span.end()`.
