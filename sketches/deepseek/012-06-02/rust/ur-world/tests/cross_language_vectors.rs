//! Both verifiers must reach the same verdict on every case in
//! the shared vector file. This is the strongest form of the
//! claim "the standard is not implementation-defined": same
//! input, same output, independent code.

use std::path::PathBuf;
use std::process::Command;

fn vector_path() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("..").join("..").join("vectors")
        .join("proof_cases.json")
}

fn run_rust(v: &PathBuf) -> std::process::Output {
    Command::new(env!("CARGO"))
        .args([
            "run", "--quiet", "--example",
            "verify_proof_offline", "--",
            &v.to_string_lossy(),
        ])
        .output()
        .expect("rust runner")
}

fn run_python(v: &PathBuf) -> Option<std::process::Output> {
    let python = std::env::var("PYTHON")
        .unwrap_or_else(|_| "python3".into());
    let script = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("examples").join("verify_proof_offline.py");
    Command::new(&python)
        .arg(&script).arg(v)
        .output().ok()
}

#[test]
fn vector_file_exists() {
    let v = vector_path();
    assert!(v.exists(),
        "vector file missing — run: python3 vectors/gen_proof_vectors.py");
}

#[test]
fn rust_passes_all_vectors() {
    let out = run_rust(&vector_path());
    let stdout = String::from_utf8_lossy(&out.stdout);
    let stderr = String::from_utf8_lossy(&out.stderr);
    assert!(out.status.success(),
        "Rust runner failed.\nstdout:\n{stdout}\nstderr:\n{stderr}");
    assert!(stdout.contains("match:    12/12"),
        "Rust runner did not match all cases:\n{stdout}");
}

#[test]
fn python_passes_all_vectors() {
    match run_python(&vector_path()) {
        None => eprintln!("python3 unavailable; skipping"),
        Some(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout);
            let stderr = String::from_utf8_lossy(&out.stderr);
            assert!(out.status.success(),
                "Python runner failed.\nstdout:\n{stdout}\nstderr:\n{stderr}");
            assert!(stdout.contains("match:    12/12"),
                "Python runner did not match all cases:\n{stdout}");
        }
    }
}

#[test]
fn both_runners_agree() {
    let v = vector_path();
    let rust = run_rust(&v);
    let python = run_python(&v);
    let rust_ok = rust.status.success();
    let python_ok = python.as_ref().map_or(true, |o| o.status.success());
    if rust_ok != python_ok {
        let rust_out = String::from_utf8_lossy(&rust.stdout);
        let python_out = python.as_ref()
            .map(|o| String::from_utf8_lossy(&o.stdout).to_string())
            .unwrap_or_default();
        panic!(
            "runners disagree:\n\
             rust_ok={rust_ok}\n\
             python_ok={python_ok}\n\
             rust stdout:\n{rust_out}\n\
             python stdout:\n{python_out}");
    }
}
