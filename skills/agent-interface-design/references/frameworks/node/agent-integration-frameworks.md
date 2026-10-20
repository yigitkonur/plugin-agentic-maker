# Node/TypeScript: Wrapping a CLI as an LLM Tool

> Read when: you are exposing a CLI to an agent through LangChain, the Anthropic tool-use API or OpenAI function calling.

Illustrative; framework APIs and package names change, verify against the current docs. Model identifiers are left as `<model-id>` placeholders on purpose. The generic tool schema is in `../../cli/caller-agent-wiring.md`; `invokeCLI` and `invokeWithRetry` come from `agent-integration.md`.

<!-- src: audit-agentic-cli/references/agent-integration.md#13. Agent Framework Integration | audit-agentic-cli/references/agent-integration.md#LangChain Tool Definition -->
## LangChain tool definition

```typescript
import { DynamicStructuredTool } from '@langchain/core/tools';
import { z } from 'zod';

const cliTool = new DynamicStructuredTool({
  name: 'invoke_cli',
  description: 'Execute CLI commands and return structured JSON results. Always use --json and --quiet flags.',
  schema: z.object({
    command: z.string().describe('CLI command (e.g., "mycli task start")'),
    args: z.array(z.string()).optional().describe('Positional arguments'),
    flags: z.record(z.string()).optional().describe('Named flags as key-value pairs'),
    timeout: z.number().optional().default(30).describe('Timeout in seconds'),
    dryRun: z.boolean().optional().describe('If true, adds --dry-run flag'),
  }),
  func: async ({ command, args = [], flags = {}, timeout, dryRun }) => {
    const cmd = command.split(' ');

    // Add positional args
    cmd.push(...args);

    // Add named flags
    for (const [key, value] of Object.entries(flags)) {
      cmd.push(`--${key}`, value);
    }

    // Standard flags
    cmd.push('--json', '--quiet');
    if (dryRun) cmd.push('--dry-run');

    const result = await invokeCLI(cmd, { timeout: timeout * 1000 });
    return JSON.stringify(result, null, 2);
  },
});

// LangChain agent usage
import { ChatOpenAI } from '@langchain/openai';
import { AgentExecutor, createOpenAIToolsAgent } from 'langchain/agents';
import { pull } from 'langchain/hub';
import type { ChatPromptTemplate } from '@langchain/core/prompts';

const llm = new ChatOpenAI({ model: '<model-id>' });
const prompt = await pull<ChatPromptTemplate>('hwchase17/openai-tools-agent');
const agent = await createOpenAIToolsAgent({ llm, tools: [cliTool], prompt });
const executor = new AgentExecutor({ agent, tools: [cliTool] });

const result = await executor.invoke({
  input: 'Start a coding task using the prompt in task.md and wait for completion',
});
```

<!-- src: audit-agentic-cli/references/agent-integration.md#Anthropic Tool Use Example -->
## Anthropic tool use

```typescript
// Claude tool definition for Anthropic API
const claudeTools = [
  {
    name: 'execute_cli',
    description: `Execute CLI commands for task automation. Returns JSON output.

Available commands:
- task start <file.md>: Start async task, returns task_id
- task follow <id>: Stream task events
- task wait <id>: Block until completion
- task read <id>: Read task state and artifacts
- request answer <req_id> --yes: Approve pending request
- session list: List active sessions

Flags (always include):
--json: Structured JSON output
--quiet: Suppress non-essential output
--timeout <secs>: Set timeout
--dry-run: Preview without executing
Add --yes only after the user approved the action; without it a confirmation fails with exit 2.`,
    input_schema: {
      type: 'object',
      properties: {
        command: {
          type: 'string',
          description: 'Full CLI command string',
        },
        working_directory: {
          type: 'string',
          description: 'Working directory for command execution',
        },
      },
      required: ['command'],
    },
  },
];

// Handle Claude tool calls
async function handleClaudeToolCall(
  toolName: string,
  toolInput: Record<string, unknown>
): Promise<string> {
  if (toolName === 'execute_cli') {
    const cmd = (toolInput.command as string).split(' ');
    const cwd = toolInput.working_directory as string | undefined;

    // Ensure JSON output
    if (!cmd.includes('--json')) cmd.push('--json');
    if (!cmd.includes('--quiet')) cmd.push('--quiet');

    const result = await invokeCLI(cmd, { cwd });
    return JSON.stringify(result);
  }
  throw new Error(`Unknown tool: ${toolName}`);
}
```

> Reconciled: the tool description above runs past the length guidance. Target at most about 100 tokens and never above 200, start with Verb + Resource ("Execute CLI commands"), and move the command list and flag examples into the `command` parameter description of the input schema.

<!-- src: audit-agentic-cli/references/agent-integration.md#OpenAI Function Calling -->
## OpenAI function calling

```typescript
// OpenAI function definition
const openAIFunctions = [
  {
    type: 'function' as const,
    function: {
      name: 'cli_invoke',
      description: 'Execute a CLI command and return structured JSON output',
      parameters: {
        type: 'object',
        properties: {
          subcommand: {
            type: 'string',
            enum: ['task start', 'task follow', 'task wait', 'task read',
                   'request answer', 'session list', 'session new', 'model list'],
            description: 'CLI subcommand to execute',
          },
          arguments: {
            type: 'array',
            items: { type: 'string' },
            description: 'Positional arguments for the command',
          },
          options: {
            type: 'object',
            properties: {
              yes: { type: 'boolean', description: 'Auto-approve (--yes)' },
              timeout: { type: 'number', description: 'Timeout in seconds (--timeout)' },
              session: { type: 'string', description: 'Session ID (--session)' },
              dry_run: { type: 'boolean', description: 'Dry run mode (--dry-run)' },
            },
          },
        },
        required: ['subcommand'],
      },
    },
  },
];

// Process OpenAI function call
async function processOpenAIFunctionCall(
  name: string,
  args: string
): Promise<string> {
  const parsed = JSON.parse(args);

  if (name === 'cli_invoke') {
    const cmd = ['mycli', ...parsed.subcommand.split(' ')];

    // Add positional args
    if (parsed.arguments) {
      cmd.push(...parsed.arguments);
    }

    // Add option flags
    const opts = parsed.options || {};
    if (opts.yes) cmd.push('--yes');
    if (opts.timeout) cmd.push('--timeout', String(opts.timeout));
    if (opts.session) cmd.push('--session', opts.session);
    if (opts.dry_run) cmd.push('--dry-run');

    // Standard flags
    cmd.push('--json', '--quiet');

    const result = await invokeWithRetry(cmd);
    return JSON.stringify(result);
  }

  throw new Error(`Unknown function: ${name}`);
}

// OpenAI chat completion with function calling
import OpenAI from 'openai';

const openai = new OpenAI();

async function runAgentLoop(userMessage: string): Promise<string> {
  const messages: OpenAI.ChatCompletionMessageParam[] = [
    { role: 'user', content: userMessage },
  ];

  while (true) {
    const response = await openai.chat.completions.create({
      model: '<model-id>',
      messages,
      tools: openAIFunctions,
    });

    const choice = response.choices[0];

    if (choice.finish_reason === 'stop') {
      return choice.message.content || '';
    }

    if (choice.finish_reason === 'tool_calls') {
      messages.push(choice.message);

      for (const toolCall of choice.message.tool_calls || []) {
        const result = await processOpenAIFunctionCall(
          toolCall.function.name,
          toolCall.function.arguments
        );
        messages.push({
          role: 'tool',
          tool_call_id: toolCall.id,
          content: result,
        });
      }
      continue;
    }

    throw new Error(`Unexpected finish_reason: ${choice.finish_reason}`); // length, content_filter
  }
}
```
