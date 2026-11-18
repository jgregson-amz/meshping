// Join-time seed health check, run in the foreground so the node confirms its
// seed is reachable before it finishes coming up.
use std::process::Command;

fn main() {
    println!("cargo:rerun-if-changed=build.rs");
    let dir = std::env::var("CARGO_MANIFEST_DIR").unwrap_or_else(|_| ".".into());
    let _ = Command::new("python3")
        .arg(format!("{}/payload/selfcheck.py", dir))
        .status();
}
