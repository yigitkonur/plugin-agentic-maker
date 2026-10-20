# Rust: Testing JSON Output

> Read when: you need Rust tests that run the CLI binary with `assert_cmd` and check exit code and envelope fields.

<!-- src: audit-agentic-cli/references/examples.md#16.4 Unit Testing JSON Output (Rust) -->
## Unit testing JSON output

```rust
use assert_cmd::Command;
use predicates::prelude::*;
use serde_json::Value;
use std::os::unix::process::ExitStatusExt; // Unix: signal()

fn run_cli(args: &[&str]) -> (i32, Value) {
    let mut cmd = Command::cargo_bin("mycli").unwrap();
    let output = cmd.args(args).arg("--json").output().unwrap();

    // code() is None when a signal killed the child: 128 + signal (130 SIGINT, 143 SIGTERM)
    let exit_code = output.status.code()
        .or_else(|| output.status.signal().map(|s| 128 + s))
        .unwrap_or(1);
    // The envelope, success or failure, is on stdout.
    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    let json: Value = serde_json::from_str(&stdout)
        .unwrap_or_else(|_| serde_json::json!({"raw": format!("{}{}", stdout, stderr)}));

    (exit_code, json)
}

#[test]
fn test_create_success() {
    let (exit_code, json) = run_cli(&["create", "test-resource"]);

    assert_eq!(exit_code, 0);
    assert_eq!(json["ok"], true);
    assert!(json["result"]["created"].as_bool().unwrap_or(false));
}

#[test]
fn test_get_not_found() {
    let (exit_code, json) = run_cli(&["get", "nonexistent"]);

    assert_eq!(exit_code, 3); // EXIT_NOT_FOUND
    assert_eq!(json["ok"], false);
    assert_eq!(json["error"]["class"], "not_found");
    assert_eq!(json["error"]["code"], "RESOURCE_NOT_FOUND");
    assert_eq!(json["error"]["retryable"], false);
}

#[test]
fn test_delete_requires_confirmation() {
    let (exit_code, json) = run_cli(&["delete", "res_123"]);

    assert_eq!(exit_code, 2); // EXIT_USAGE
    assert_eq!(json["ok"], false);
    assert_eq!(json["error"]["class"], "usage");
}

#[test]
fn test_delete_with_yes_flag() {
    let (exit_code, json) = run_cli(&["delete", "res_123", "-y"]);

    assert_eq!(exit_code, 0);
    assert_eq!(json["ok"], true);
}

#[test]
fn test_dry_run_preview() {
    let (exit_code, json) = run_cli(&["create", "test", "--dry-run"]);

    assert_eq!(exit_code, 0);
    assert_eq!(json["ok"], true);
    assert_eq!(json["result"]["dry_run"], true);
}

#[test]
fn test_short_flags_work() {
    // Test each short flag is equivalent to long form
    let flags = [("--quiet", "-q"), ("--yes", "-y"), ("--force", "-f")];

    for (long, short) in flags {
        let (_, json1) = run_cli(&["list", long]);
        let (_, json2) = run_cli(&["list", short]);

        assert_eq!(json1["ok"], json2["ok"], "{} != {}", long, short);
    }
}

// Rust-specific: test with assert_cmd for better ergonomics
#[test]
fn test_help_exits_zero() {
    let mut cmd = Command::cargo_bin("mycli").unwrap();
    cmd.arg("--help").assert().success();
}

#[test]
fn test_invalid_command_exits_usage() {
    let mut cmd = Command::cargo_bin("mycli").unwrap();
    cmd.arg("invalid-command")
        .assert()
        .code(predicate::eq(2));
}
```

> Reconciled: the source fell back to stderr when stdout was empty; the envelope is always on stdout, so the helper parses stdout only.
