//! Run proof vector cases against the Rust verifier.
//!
//! Usage: verify_proof_offline <vector_file>
//! Exit 0 iff every case's outcome matches its 'expected' field.

mod common;

use std::env;
use std::fs;
use std::path::PathBuf;

use serde::Deserialize;
use serde_json::Value;

use common::verify_proof;

#[derive(Deserialize)]
struct Vector {
    identity: Identity,
    cases: Vec<Case>,
}

#[derive(Deserialize)]
struct Identity {
    did: String,
}

#[derive(Deserialize)]
struct Case {
    id: String,
    description: String,
    body: Value,
    proof: Value,
    expected_did: String,
    expected: String,
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("Usage: verify_proof_offline <vector_file>");
        std::process::exit(2);
    }
    let path = PathBuf::from(&args[1]);
    let text = fs::read_to_string(&path)
        .unwrap_or_else(|e| {
            eprintln!("read {}: {e}", path.display());
            std::process::exit(2);
        });
    let v: Vector = serde_json::from_str(&text)
        .unwrap_or_else(|e| {
            eprintln!("parse {}: {e}", path.display());
            std::process::exit(2);
        });

    let mut matched = 0;
    let mut mismatches: Vec<String> = Vec::new();
    for case in &v.cases {
        let result = verify_proof(
            &case.body, &case.proof, &case.expected_did);
        let got = if result.is_ok() { "pass" } else { "fail" };
        if got == case.expected {
            matched += 1;
        } else {
            let err = result.err().unwrap_or_default();
            mismatches.push(format!(
                "  [{}] expected {} got {}: {}",
                case.id, case.expected, got, err));
        }
    }

    println!("=== vector runner (Rust) ===");
    println!("  identity: {}", v.identity.did);
    println!("  cases:    {}", v.cases.len());
    println!("  match:    {}/{}", matched, v.cases.len());
    if !mismatches.is_empty() {
        println!();
        println!("  mismatches:");
        for m in &mismatches {
            println!("{m}");
        }
        std::process::exit(1);
    }
}
