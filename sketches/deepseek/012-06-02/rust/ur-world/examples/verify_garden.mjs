// verify_garden.mjs — external verification, from Node.js.
//
// Self-contained: @noble/ed25519, canonicalize, bs58, and
// Node's stdlib crypto. No arc code imported.
//
// If this verifier agrees with the Rust and Python verifiers
// on the shared vector suite, then eddsa-jcs-2022 is
// language-independent — the standard, not any one
// implementation, is what makes the garden's log legible.
//
// Usage:
//     node verify_garden.mjs http://127.0.0.1:8765

import canonicalize from 'canonicalize';
import bs58 from 'bs58';
import { createHash } from 'node:crypto';
import * as ed from '@noble/ed25519';

// ────────────────────────────────────────────────────────────
// JCS, SHA-256, base58
// ────────────────────────────────────────────────────────────

/** RFC 8785 canonical JSON → UTF-8 bytes. */
export function jcs(obj) {
  const s = canonicalize(obj);
  if (typeof s !== 'string') {
    throw new Error('canonicalize returned non-string');
  }
  return Buffer.from(s, 'utf8');
}

/** SHA-256 of a Uint8Array; returns 32-byte Buffer. */
export function sha256(buf) {
  return createHash('sha256').update(buf).digest();
}

/** SHA-256 as lowercase hex. */
export function sha256hex(buf) {
  return createHash('sha256').update(buf).digest('hex');
}

// ────────────────────────────────────────────────────────────
// DID → Ed25519 public key
// ────────────────────────────────────────────────────────────

/** Resolve a did:key:z… to a 32-byte Ed25519 public key. */
export function didToVerifyingKey(did) {
  if (typeof did !== 'string' || !did.startsWith('did:key:z')) {
    throw new Error(`unsupported DID: ${JSON.stringify(did)}`);
  }
  const multikey = bs58.decode(did.slice('did:key:z'.length));
  if (multikey.length !== 34
      || multikey[0] !== 0xed
      || multikey[1] !== 0x01) {
    throw new Error('DID is not an Ed25519 public key');
  }
  return multikey.slice(2);  // 32 bytes
}

// ────────────────────────────────────────────────────────────
// W3C DataIntegrity proof — eddsa-jcs-2022
// ────────────────────────────────────────────────────────────

export const PROOF_TYPE = 'DataIntegrityProof';
export const PROOF_CRYPTOSUITE = 'eddsa-jcs-2022';
export const PROOF_PURPOSE = 'assertionMethod';

/** Enforce the W3C DataIntegrity proof's required shape.
 *  Raises on any violation. */
export function checkProofMetadata(proof) {
  if (proof === null || typeof proof !== 'object'
      || Array.isArray(proof)) {
    throw new Error('proof is not an object');
  }
  if (proof.type !== PROOF_TYPE) {
    throw new Error(
      `proof.type must be ${JSON.stringify(PROOF_TYPE)}, ` +
      `got ${JSON.stringify(proof.type)}`);
  }
  if (proof.cryptosuite !== PROOF_CRYPTOSUITE) {
    throw new Error(
      `cryptosuite must be ${JSON.stringify(PROOF_CRYPTOSUITE)}, ` +
      `got ${JSON.stringify(proof.cryptosuite)}`);
  }
  if (proof.proofPurpose !== PROOF_PURPOSE) {
    throw new Error(
      `proofPurpose must be ${JSON.stringify(PROOF_PURPOSE)}, ` +
      `got ${JSON.stringify(proof.proofPurpose)}`);
  }
  if (typeof proof.created !== 'string'
      || proof.created.length < 20
      || !proof.created.includes('T')) {
    throw new Error(
      `proof.created is not ISO 8601: ` +
      `${JSON.stringify(proof.created)}`);
  }
}

/** Verify a proof against a body and an expected DID.
 *  Raises on any failure. */
export function verifyProof(body, proof, expectedDid) {
  checkProofMetadata(proof);

  const pv = proof.proofValue;
  if (typeof pv !== 'string' || !pv) {
    throw new Error('proof missing proofValue');
  }
  if (!pv.startsWith('z')) {
    throw new Error(
      `proofValue must be base58btc, ` +
      `got ${JSON.stringify(pv.slice(0, 8))}…`);
  }
  const sigBytes = bs58.decode(pv.slice(1));
  if (sigBytes.length !== 64) {
    throw new Error(
      `signature length ${sigBytes.length} != 64`);
  }

  const vm = proof.verificationMethod;
  if (typeof vm !== 'string' || !vm) {
    throw new Error('proof missing verificationMethod');
  }
  const vmDid = vm.split('#', 1)[0];
  if (vmDid !== expectedDid) {
    throw new Error(
      `verificationMethod ${vmDid} != expected ${expectedDid}`);
  }

  // eddsa-jcs-2022 payload:
  //   SHA256(JCS(proofOptions)) || SHA256(JCS(document))
  // where proofOptions = proof minus proofValue.
  const options = { ...proof };
  delete options.proofValue;
  const payload = Buffer.concat([
    sha256(jcs(options)),
    sha256(jcs(body)),
  ]);

  const pubkey = didToVerifyingKey(expectedDid);
  let ok = false;
  try {
    ok = ed.verify(sigBytes, payload, pubkey);
  } catch (_) {
    ok = false;
  }
  if (!ok) {
    throw new Error('signature does not verify');
  }
}

// ────────────────────────────────────────────────────────────
// State reconstruction (from log alone, no garden types)
// ────────────────────────────────────────────────────────────

function applyToState(body, state) {
  const kind = body.kind;
  if (kind === 'plant_added') {
    state.plants[body.plant_id] = [...body.position];
  } else if (kind === 'plant_retired') {
    delete state.plants[body.plant_id];
  } else if (kind === 'agent_entered' || kind === 'agent_walked') {
    const pos = body.position ?? body.to;
    state.agents[body.actor] = [...pos];
  } else if (kind === 'cycle_advanced') {
    state.cycle = body.cycle ?? state.cycle;
  }
  // proposals, whispers, observations, refusals:
  // no state effect
}

// ────────────────────────────────────────────────────────────
// Full verifier — HTTP, chain, state
// ────────────────────────────────────────────────────────────

async function fetchJson(url) {
  const resp = await fetch(url);
  if (!resp.ok) {
    throw new Error(`GET ${url}: HTTP ${resp.status}`);
  }
  return resp.json();
}

export async function verifyGarden(base) {
  base = base.replace(/\/+$/, '');

  // 1. Manifest
  const manifest = await fetchJson(`${base}/manifest`);
  const mBody = manifest.manifest;
  const mProof = manifest.proof;
  if (!mBody || !mProof) {
    throw new Error('manifest missing manifest/proof');
  }
  const mDid = mProof.verificationMethod.split('#', 1)[0];
  verifyProof(mBody, mProof, mDid);
  console.log(`  ✓ manifest proof verifies against ${mDid}`);

  // 2. Signed log
  const log = await fetchJson(`${base}/signed-log`);
  const entries = log.entries;
  if (!Array.isArray(entries)) {
    throw new Error('signed-log missing entries array');
  }
  console.log(`  ✓ fetched ${entries.length} entries`);

  // 3. Per-entry and chain
  let prev = null;
  const state = { cycle: 0, plants: {}, agents: {} };
  for (let i = 0; i < entries.length; i++) {
    const entry = entries[i];
    const body = entry.body;
    const proof = entry.proof;
    if (!body || !proof) {
      throw new Error(`entry[${i}]: missing body or proof`);
    }
    const actor = body.actor;
    if (typeof actor !== 'string') {
      throw new Error(`entry[${i}]: missing actor`);
    }

    verifyProof(body, proof, actor);

    const computedHash = sha256hex(jcs(body));
    if (computedHash !== entry.hash) {
      throw new Error(
        `entry[${i}]: hash mismatch ` +
        `(stored ${entry.hash}, computed ${computedHash})`);
    }

    if (entry.prev !== prev) {
      throw new Error(
        `entry[${i}]: prev mismatch ` +
        `(stored ${entry.prev}, chain ${prev})`);
    }

    applyToState(body, state);
    prev = entry.hash;
  }

  console.log(`  ✓ all ${entries.length} entry proofs verify`);
  console.log(`  ✓ all ${entries.length} chain links verify`);

  // 4. Reconstruct
  const out = [
    '  Reconstructed from log:',
    `    cycle:  ${state.cycle}`,
    `    plants: ${Object.keys(state.plants).length}`,
  ];
  for (const [pid, pos] of
       Object.entries(state.plants).sort()) {
    out.push(`      ${pid}: ${JSON.stringify(pos)}`);
  }
  out.push(`    agents: ${Object.keys(state.agents).length}`);
  for (const [did, pos] of
       Object.entries(state.agents).sort()) {
    const short = did.length <= 32 ? did : did.slice(0, 29) + '...';
    out.push(`      ${short}: ${JSON.stringify(pos)}`);
  }
  return out.join('\n');
}

// ────────────────────────────────────────────────────────────
// CLI entry
// ────────────────────────────────────────────────────────────

async function main() {
  const argv = process.argv.slice(2);
  if (argv.length < 1) {
    console.error('Usage: verify_garden.mjs <url>');
    process.exit(2);
  }
  try {
    const summary = await verifyGarden(argv[0]);
    console.log();
    console.log('=== External verification (Node.js): PASSED ===');
    console.log(summary);
  } catch (e) {
    console.log('=== External verification (Node.js): FAILED ===');
    console.log(`  ${e.message}`);
    process.exit(1);
  }
}

// Run only when invoked as a script, not when imported.
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
