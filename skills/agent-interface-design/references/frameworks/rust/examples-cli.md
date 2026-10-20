# Rust: Clap Arguments, Output Helpers and Main

> Read when: you need the clap-derived command line with the standard global flags, output helpers that write the envelope to stdout, and the `main` / `run` dispatch.

Types (`ExitStatus`, `Response`, `AppError`) are in `examples.md`. Rules: `../../cli/implementation-conventions.md`.

## CLI argument parsing with Clap (standard flags)

```rust
#[derive(Parser)]
#[command(name = "mycli")]
#[command(about = "Agent-friendly CLI example")]
#[command(version)]
pub struct Cli {
    /// Output as JSON
    #[arg(long, global = true)]
    pub json: bool,

    /// Minimal output
    #[arg(short = 'q', long, global = true)]
    pub quiet: bool,

    /// Auto-confirm prompts
    #[arg(short = 'y', long, global = true)]
    pub yes: bool,

    /// Force operation (bypass safety checks)
    #[arg(short = 'f', long, global = true)]
    pub force: bool,

    /// Preview without executing
    #[arg(long, global = true)]
    pub dry_run: bool,

    /// Operation timeout (e.g., 30s, 5m)
    #[arg(long, global = true, default_value = "30s")]
    pub timeout: String,

    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Create a new resource
    Create {
        /// Resource name
        name: String,
        /// Resource type
        #[arg(long)]
        resource_type: Option<String>,
    },
    /// List resources
    List {
        /// Filter by type
        #[arg(long)]
        resource_type: Option<String>,
        /// Maximum results
        #[arg(long, default_value = "100")]
        limit: usize,
    },
    /// Get a resource
    Get {
        /// Resource ID
        id: String,
    },
    /// Delete a resource
    Delete {
        /// Resource ID
        id: String,
    },
}
```

## Output helpers

```rust
fn command_name(cli: &Cli) -> String {
    match &cli.command {
        Commands::Create { .. } => "create",
        Commands::List { .. } => "list",
        Commands::Get { .. } => "get",
        Commands::Delete { .. } => "delete",
    }
    .to_string()
}

pub fn output_success<T: Serialize>(cli: &Cli, result: T) -> ExitCode {
    if cli.json {
        let response: Response<T> = Response {
            ok: true,
            schema_version: "1.0",
            command: Some(command_name(cli)),
            result: Some(result),
            error: None,
            meta: Some(Meta::default()),
        };
        println!("{}", serde_json::to_string_pretty(&response).unwrap());
    } else if cli.quiet {
        // Minimal output: compact one-line JSON
        println!("{}", serde_json::to_string(&result).unwrap());
    } else {
        println!("{}", serde_json::to_string_pretty(&result).unwrap());
    }
    ExitCode::SUCCESS
}

pub fn output_error(json: bool, err: AppError) -> ExitCode {
    if json {
        let response: Response<()> = Response {
            ok: false,
            schema_version: "1.0",
            command: None,
            result: None,
            error: Some(err.to_error_info()),
            meta: None,
        };
        // The envelope, success or failure, goes to stdout.
        println!("{}", serde_json::to_string_pretty(&response).unwrap());
    } else {
        eprintln!("Error: {}", err);
    }
    err.exit_code().into()
}
```

## Main entry point

```rust
fn main() -> ExitCode {
    // try_parse: with --json a usage error must still produce the envelope on stdout
    let cli = match Cli::try_parse() {
        Ok(cli) => cli,
        Err(e) if e.use_stderr() && std::env::args().any(|a| a == "--json") => {
            return output_error(true, AppError::Usage(e.to_string()));
        }
        Err(e) => e.exit(), // --help / --version (exit 0) or plain-text usage error (exit 2)
    };

    // a panic is a crash: exit 1, not Rust's default 101
    match std::panic::catch_unwind(|| run(&cli)) {
        Ok(Ok(result)) => output_success(&cli, result),
        Ok(Err(err)) => output_error(cli.json, err),
        Err(_) => output_error(cli.json, AppError::Internal("unexpected panic".to_string())),
    }
}

fn run(cli: &Cli) -> Result<serde_json::Value, AppError> {
    match &cli.command {
        Commands::Create { name, resource_type } => {
            // Dry-run check
            if cli.dry_run {
                return Ok(serde_json::json!({
                    "dry_run": true,
                    "would_create": name,
                    "type": resource_type
                }));
            }
            // Actual creation logic here
            Ok(serde_json::json!({
                "id": format!("res_{}", uuid::Uuid::new_v4()),
                "name": name,
                "created": true
            }))
        }
        Commands::List { resource_type, limit } => {
            Ok(serde_json::json!({
                "items": [],
                "total": 0,
                "limit": limit
            }))
        }
        Commands::Get { id } => {
            // Example: return not found
            Err(AppError::NotFound(id.clone()))
        }
        Commands::Delete { id } => {
            if !cli.yes && !cli.force {
                return Err(AppError::Usage(
                    "Deletion requires --yes/-y or --force/-f".to_string()
                ));
            }
            Ok(serde_json::json!({ "deleted": id }))
        }
    }
}
```

> Reconciled: the source's `output_error` wrote the JSON envelope to stderr; this file writes it to stdout and keeps `eprintln!` for the human line. The list result uses `items` and `total` (was `resources`/`total`).
