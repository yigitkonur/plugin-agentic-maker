# Rust: Exit Status, Envelope and Error Types

> Read when: you need Rust code for the exit-code enum, the serde-serialized JSON envelope and a `thiserror` error type that maps to class, code, retryability and exit status.

Rules: `../../cli/exit-codes.md`, `../../cli/envelope-and-errors.md`, `../../cli/error-classes.md`. The clap arguments, output helpers and `main` are in `examples-cli.md`; tests in `examples-tests.md`.

<!-- src: audit-agentic-cli/references/examples.md#14. Structured Output (Rust with Serde + Clap) -->
## Structured output

A complete Rust CLI implementing the standard patterns. This file holds the first half (types); `examples-cli.md` holds the second.

```rust
use clap::{Parser, Subcommand};
use serde::{Deserialize, Serialize};
use std::process::ExitCode;
use thiserror::Error;

// ============================================================================
// Exit Codes (matching standard 0-8)
// ============================================================================

#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum ExitStatus {
    Success = 0,
    Crash = 1,
    UsageError = 2,
    NotFound = 3,
    Auth = 4,
    Conflict = 5,
    ValidationError = 6,
    TransientError = 7,
    Partial = 8,
}

impl From<ExitStatus> for ExitCode {
    fn from(status: ExitStatus) -> Self {
        ExitCode::from(status as u8)
    }
}

// ============================================================================
// Standard JSON Envelope
// ============================================================================

#[derive(Debug, Serialize)]
pub struct Response<T: Serialize> {
    pub ok: bool,
    pub schema_version: &'static str, // "1.0"
    #[serde(skip_serializing_if = "Option::is_none")]
    pub command: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub result: Option<T>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub error: Option<ErrorInfo>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub meta: Option<Meta>,
}

#[derive(Debug, Serialize)]
pub struct ErrorInfo {
    pub class: String,
    pub code: String,
    pub message: String,
    pub retryable: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub suggestion: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub details: Option<serde_json::Value>,
}

#[derive(Debug, Serialize, Default)]
pub struct Meta {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub truncated: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub total_count: Option<usize>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_ms: Option<u64>,
}

// ============================================================================
// Error Handling with thiserror
// ============================================================================

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Resource '{0}' not found")]
    NotFound(String),

    #[error("Resource '{0}' already exists")]
    Conflict(String),

    #[error("Authentication failed: {0}")]
    AuthFailed(String),

    #[error("Validation failed: {0}")]
    ValidationFailed(String),

    #[error("Network error: {0}")]
    Transient(String),

    #[error("Usage error: {0}")]
    Usage(String),

    #[error("Internal error: {0}")]
    Internal(String),
}

impl AppError {
    pub fn exit_code(&self) -> ExitStatus {
        match self {
            AppError::NotFound(_) => ExitStatus::NotFound,
            AppError::Conflict(_) => ExitStatus::Conflict,
            AppError::AuthFailed(_) => ExitStatus::Auth,
            AppError::ValidationFailed(_) => ExitStatus::ValidationError,
            AppError::Transient(_) => ExitStatus::TransientError,
            AppError::Usage(_) => ExitStatus::UsageError,
            AppError::Internal(_) => ExitStatus::Crash,
        }
    }

    pub fn error_class(&self) -> &'static str {
        match self {
            AppError::NotFound(_) => "not_found",
            AppError::Conflict(_) => "conflict",
            AppError::AuthFailed(_) => "auth",
            AppError::ValidationFailed(_) => "validation",
            AppError::Transient(_) => "network",
            AppError::Usage(_) => "usage",
            AppError::Internal(_) => "internal",
        }
    }

    pub fn error_code(&self) -> &'static str {
        match self {
            AppError::NotFound(_) => "RESOURCE_NOT_FOUND",
            AppError::Conflict(_) => "RESOURCE_EXISTS",
            AppError::AuthFailed(_) => "AUTH_FAILED",
            AppError::ValidationFailed(_) => "VALIDATION_FAILED",
            AppError::Transient(_) => "NETWORK_ERROR",
            AppError::Usage(_) => "USAGE_ERROR",
            AppError::Internal(_) => "INTERNAL_ERROR",
        }
    }

    pub fn is_retryable(&self) -> bool {
        matches!(self, AppError::Transient(_))
    }

    pub fn to_error_info(&self) -> ErrorInfo {
        ErrorInfo {
            class: self.error_class().to_string(),
            code: self.error_code().to_string(),
            message: self.to_string(),
            retryable: self.is_retryable(),
            suggestion: None,
            details: None,
        }
    }
}
```

<!-- src: audit-agentic-cli/references/examples.md#Cargo.toml Dependencies -->
## Cargo.toml dependencies

```toml
[dependencies]
clap = { version = "4", features = ["derive"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
thiserror = "1"
uuid = { version = "1", features = ["v4"] }
```

> Note: the enum uses `Crash` for 1, `Auth` for 4 and `Partial = 8`. The network error has class `network` with code `NETWORK_ERROR` (`transient` is the exit-7 group, not a class). Check the versions in `Cargo.toml` before use.
