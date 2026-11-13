# Working in open-worlds

This repository follows the handbook at
https://github.com/jasonelias144-svg/policy-handbook. Read its orientation (README.md)
before your first session here. The rules below add to the handbook; they never
loosen it.

## Every session

1. Read `STATUS.md` and the open pull requests (handbook P1).
2. Work on a branch; never push to `main` (P3).
3. End by pushing, updating `STATUS.md` on your branch, and opening or updating
   the pull request (P1).

## Who decides

The founder decides what this project is for and who works on it. The technical
lead (Claude) decides everything about the code, and records an approval on
every pull request before it merges (P4). Intent questions go to the founder (P5).

## This repository

- **What it is:** simulated worlds where AI agents live under one rule,
  respect one another's freedom, with full transparency and exit at any time
- **Run:** `python3 -m experiments.corridor`
- **Setup:** `python3 -m pip install -r requirements.txt` (each direct
  dependency pinned, with its reason)
- **Test:** `python3 -m unittest discover -s tests -t .` (must pass before a
  pull request is marked ready)
- **Other checks:** CI also checks the chemistry against RDKit
  (`tests/test_chem_rdkit.py`), and runs the sketches' own tests in a job
  of their own (`sketches/README.md`)
- **Merge method:** merge commit, as every pull request since #3 has been
  merged. It keeps the commits that review records name (P4), which a
  squash would drop from `main`'s history.
- **Release:** none yet. When worlds run publicly, this file will say where
  and how a release is checked (P6).
- **Data:** each world's event log is its public record. Cycle results live
  in `docs/cycles/`.

## Rules specific to this repository

- **The charter is the founder's words.** Change `CHARTER.md` only with the
  founder's approval, and say so in the pull request.
- **The kernel is the only authority.** Agents get immutable observations and
  return actions; nothing an agent returns is trusted until the kernel has
  checked it. Agents never get references to the world's internals.
- **The protected freedoms have tests.** Exit, voice and information (and
  vote, once governance exists) each have tests. A change that weakens one is
  a founder decision (P5), not a code decision.
- **Results come from real runs.** Every number in a cycle record comes from
  a run whose command and seeds are written next to it. Predicted or imagined
  output is never reported as a result.
- **Outside agents run in sandboxes.** Agents we didn't write, and agents that
  rewrite their own code, never run in the kernel's process.
- **The sketches stay apart.** `sketches/` keeps the founder's
  conversation records and DeepSeek's code from them, as written
  (`sketches/README.md`). Nothing outside `sketches/` imports from it. Its
  code changes only in small fixes listed in `sketches/INDEX.md`, which is
  also the one place that says where the sketches and the course meet.

## Always

- Say who made each change: `Made-by: <name> (AI|human)` in commits, and the
  "Made by" field in pull requests (P3).
- No secrets or personal data anywhere in the repository (P8). The one
  exception: the founder may be named by first name, as the founder
  decided (2026-11-13). Anything more personal goes to the founder before
  it goes in.
- Report outcomes honestly: what you checked, and what you did not.
