// verify_proof_offline.mjs — run proof vector cases against
// the Node.js verifier.
//
// Usage: node verify_proof_offline.mjs <vector_file>
// Exit 0 iff every case's outcome matches its 'expected' field.

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { verifyProof } from './verify_garden.mjs';

function main(vectorPath) {
  const v = JSON.parse(fs.readFileSync(vectorPath, 'utf8'));
  if (!Array.isArray(v.cases)) {
    throw new Error('vector file missing cases array');
  }
  let matched = 0;
  const mismatches = [];

  for (const c of v.cases) {
    let got, err;
    try {
      verifyProof(c.body, c.proof, c.expected_did);
      got = 'pass';
    } catch (e) {
      got = 'fail';
      err = e.message;
    }
    if (got === c.expected) {
      matched++;
    } else {
      let msg = `  [${c.id}] expected ${c.expected} got ${got}`;
      if (err) msg += `: ${err}`;
      mismatches.push(msg);
    }
  }

  console.log('=== vector runner (Node.js) ===');
  console.log(`  identity: ${v.identity.did}`);
  console.log(`  cases:    ${v.cases.length}`);
  console.log(`  match:    ${matched}/${v.cases.length}`);

  if (mismatches.length > 0) {
    console.log();
    console.log('  mismatches:');
    for (const m of mismatches) console.log(m);
    process.exit(1);
  }
}

const scriptPath = fileURLToPath(import.meta.url);
if (process.argv[1] === scriptPath) {
  const vectorPath = process.argv[2];
  if (!vectorPath) {
    console.error('Usage: node verify_proof_offline.mjs <vector_file>');
    process.exit(2);
  }
  main(vectorPath);
}
