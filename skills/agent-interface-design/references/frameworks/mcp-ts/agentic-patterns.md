# Dependency Chains, Available Actions and Guard Tools in TypeScript

> Read when: you are enforcing tool order through required inputs, returning state-based actions, or guarding a destructive tool in TypeScript.

Explanation and rules: ../../mcp/patterns-guarded-workflows.md and ../../decisions/steering-contract.md

## Pattern 1: Parameter Dependency Chains

```typescript
// Step 1: run_tests returns a signed token
server.tool("run_tests", "Run test suite. Returns test_token required for deployment.", {
  suite: z.string(),
}, async ({ suite }) => {
  const results = await runTestSuite(suite);
  if (results.failed > 0) {
    return { content: [{ type: "text", text: `Tests failed: ${results.failed} failures` }], isError: true };
  }
  // Sign a token proving tests passed
  const testToken = sign({ suite, passed: true, ts: Date.now() }, process.env.TOKEN_SECRET!);
  return {
    content: [{ type: "text", text: `All ${results.passed} tests passed.\ntest_token: ${testToken}\n\nNow call deploy_service with this test_token.` }]
  };
});

// Step 2: deploy_service REQUIRES the token from step 1
server.tool("deploy_service", "Deploy to production. Requires test_token from run_tests.", {
  service_name: z.string(),
  environment: z.enum(["staging", "production"]),
  test_token: z.string().describe("Token returned by run_tests. Required."),
}, async ({ service_name, environment, test_token }) => {
  const payload = verify(test_token, process.env.TOKEN_SECRET!);
  if (!payload?.passed) {
    return { content: [{ type: "text", text: "Invalid test_token. Run run_tests first." }], isError: true };
  }
  await deployService(service_name, environment);
  return { content: [{ type: "text", text: `Deployed ${service_name} to ${environment}.` }] };
});
```

## Pattern 2: HATEOAS: State-Based Available Actions

```typescript
type Action = { tool: string; description: string; required_params?: string[] };

function getAvailableActions(deployment: Deployment): Action[] {
  if (deployment.status === "running") {
    return [
      { tool: "get_metrics", description: "View live metrics", required_params: ["deployment_id"] },
      { tool: "rollback_deployment", description: "Roll back to previous version", required_params: ["deployment_id"] },
      { tool: "scale_deployment", description: "Adjust instance count", required_params: ["deployment_id", "replicas"] },
    ];
  }
  if (deployment.status === "failed") {
    return [
      { tool: "get_logs", description: "Inspect failure logs", required_params: ["deployment_id"] },
      { tool: "rollback_deployment", description: "Restore last known good version", required_params: ["deployment_id"] },
    ];
  }
  if (deployment.status === "stopped") {
    return [
      { tool: "start_deployment", description: "Start the service", required_params: ["deployment_id"] },
    ];
  }
  return [];
}

server.tool("get_deployment", "Get deployment status", {
  deployment_id: z.string(),
}, async ({ deployment_id }) => {
  const deployment = await fetchDeployment(deployment_id);
  return {
    content: [{
      type: "text",
      text: JSON.stringify({
        ...deployment,
        _available_actions: getAvailableActions(deployment),
      }, null, 2)
    }]
  };
});
```

## Pattern 3: Guard Tools: Precondition Validation via Boolean Params

```typescript
server.tool(
  "delete_environment",
  "Permanently delete a deployment environment. Set tests_verified=true only after running validate_environment. Set backup_confirmed=true only after create_backup completes.",
  {
    environment_id: z.string(),
    tests_verified: z.boolean()
      .describe("Set true only after validate_environment returned no critical errors."),
    backup_confirmed: z.boolean()
      .describe("Set true only after create_backup returned a valid backup_id."),
    backup_id: z.string().optional()
      .describe("The backup_id from create_backup. Required when backup_confirmed=true."),
  },
  async ({ environment_id, tests_verified, backup_confirmed, backup_id }) => {
    if (!tests_verified) {
      return {
        content: [{ type: "text", text: "Blocked: tests_verified is false. Run validate_environment first and confirm no critical errors." }],
        isError: true,
      };
    }
    if (!backup_confirmed || !backup_id) {
      return {
        content: [{ type: "text", text: "Blocked: backup_confirmed is false or backup_id is missing. Run create_backup first." }],
        isError: true,
      };
    }
    // Optionally: cryptographically verify the backup_id is genuine
    const backupValid = await verifyBackupExists(backup_id);
    if (!backupValid) {
      return {
        content: [{ type: "text", text: `Blocked: backup_id "${backup_id}" not found or expired. Re-run create_backup.` }],
        isError: true,
      };
    }

    await deleteEnvironment(environment_id);
    return { content: [{ type: "text", text: `Environment ${environment_id} deleted.` }] };
  }
);
```
