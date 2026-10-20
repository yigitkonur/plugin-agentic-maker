# Rust: Exit Code Enum

> Read when: you are defining exit codes for a Rust (clap) CLI.

## Exit code enum

The table it implements is `../../cli/exit-codes.md`. Convert with `std::process::exit(code as i32)`.

```rust
// exitcodes.rs
pub enum ExitCode {
    Success = 0,    // Operation completed successfully
    Crash = 1,      // Unexpected error, internal failure
    Usage = 2,      // Bad flags, invalid arguments
    NotFound = 3,   // Resource does not exist
    Auth = 4,       // Authentication/authorization failed
    Conflict = 5,   // Resource conflict (exists, version mismatch)
    Validation = 6, // Input validation failed
    Transient = 7,  // Retryable error (network, timeout, rate limit)
    Partial = 8,    // Partial success (some operations failed)
}
```
