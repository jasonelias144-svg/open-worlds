//! The command: one request on standard input, the world's log on
//! standard output. A refused request exits with 1, its reason on
//! standard error (`plant_wasi::respond`).

use std::io::{Read, Write};
use std::process::ExitCode;

fn main() -> ExitCode {
    let mut request = String::new();
    let answer = std::io::stdin()
        .read_to_string(&mut request)
        .map_err(|e| format!("the request can't be read: {e}"))
        .and_then(|_| plant_wasi::respond(&request));
    match answer {
        Ok(log) => match std::io::stdout().write_all(log.as_bytes()) {
            Ok(()) => ExitCode::SUCCESS,
            Err(_) => ExitCode::FAILURE,
        },
        Err(why) => {
            let _ = writeln!(std::io::stderr(), "{why}");
            ExitCode::FAILURE
        }
    }
}
