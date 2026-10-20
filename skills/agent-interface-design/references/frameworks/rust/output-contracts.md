# Rust: Exit Code Enum

> Read when: you are defining exit codes for a Rust (clap) CLI.

## Exit code enum

The table it implements is `../../cli/exit-codes.md`. Named `ExitStatus` so it does not collide with `std::process::ExitCode`; `examples.md` converts it with `ExitCode::from(status as u8)`.

```rust
// exitcodes.rs
#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum ExitStatus {
    Success = 0,         // Operation completed successfully
    Crash = 1,           // Unexpected error, internal failure
    UsageError = 2,      // Bad flags, invalid arguments
    NotFound = 3,        // Resource does not exist
    Auth = 4,            // Authentication/authorization failed
    Conflict = 5,        // Resource conflict (exists, version mismatch)
    ValidationError = 6, // Input validation failed
    TransientError = 7,  // Retryable error (network, timeout, rate limit)
    Partial = 8,         // Partial success (some operations failed)
}
```
