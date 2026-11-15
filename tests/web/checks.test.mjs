// tests/web/checks.test.mjs
// The web app's shared checks (web/lib/checks.js), run in Node against the
// shared vectors: the same file the pages load in the browser, read here
// as a script, as a browser reads it. Run with `node --test tests/web/`.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { generateKeyPairSync, sign as edSign } from "node:crypto";
import vm from "node:vm";

const root = new URL("../../", import.meta.url);
const read = path => readFileSync(new URL(path, root), "utf8");
const json = path => JSON.parse(read(path));

const context = vm.createContext({ crypto: globalThis.crypto, TextEncoder });
const OW = vm.runInContext(read("web/lib/checks.js") + "\n;OpenWorlds", context);
const HEAD = "open-worlds/log-head/v1", BIRTH = "open-worlds/world-birth/v1";

const urLog = json("vectors/ur-garden-log.json");
const urHead = json("vectors/ur-garden-head.json");
const hosted = json("vectors/ur-garden-hosted.json");
const plants = json("vectors/plant-world.json");
const copy = v => JSON.parse(JSON.stringify(v));

// A fresh key, and a record signed with it the standard way, so a record
// the schema refuses can carry a signature that holds.
function freshKey() {
  const { publicKey, privateKey } = generateKeyPairSync("ed25519");
  const raw = Buffer.from(publicKey.export({ format: "jwk" }).x, "base64url");
  const did = "did:key:z" + OW.base58encode(Uint8Array.from([0xed, 0x01, ...raw]));
  return { did, privateKey };
}
async function signed(record, key, proofExtra = {}) {
  const proof = {
    type: "DataIntegrityProof", cryptosuite: "eddsa-jcs-2022", created: "2026-11-15T00:00:00Z",
    verificationMethod: key.did + "#" + key.did.slice(8), proofPurpose: "assertionMethod", ...proofExtra,
  };
  const data = new Uint8Array(64);
  data.set(await OW.sha256(OW.text(OW.jcs(proof))), 0);
  data.set(await OW.sha256(OW.text(OW.jcs(record))), 32);
  const signature = edSign(null, data, key.privateKey);
  return { ...record, proof: { ...proof, proofValue: "z" + OW.base58encode(signature) } };
}
const headFor = (key, log) => {
  const last = log[log.length - 1];
  return { format: HEAD, world: key.did, length: log.length, last: last.hash, tick: last.tick };
};

test("the shared vectors' logs hold, and their heads and birth records are signed", async () => {
  assert.equal(await OW.chainProblem(urLog), null);
  assert.equal(await OW.signedBy(urHead, urLog[0].data.world, HEAD), "ok");
  for (const file of [hosted, plants]) {
    for (const w of file.worlds) {
      const key = w.log[0].data.world;
      assert.equal(await OW.chainProblem(w.log), null, w.name);
      assert.equal(await OW.signedBy(w.head, key, HEAD), "ok", w.name);
      assert.equal(await OW.signedBy(w.birth, key, BIRTH), "ok", w.name);
      assert.ok(OW.covers(w.head, w.log), w.name);
      assert.equal(OW.dialsProblem(w.birth, file.template, w.log[0].data.dials), null, w.name);
    }
    assert.equal(await OW.recordHash(file.template), file.templateHash);
    assert.equal(await OW.recordHash(file.law), file.lawHash);
  }
});

test("a head covers a log when its tick isn't before the last entry's", () => {
  // The Ur-world's head was signed at tick 28; its last entry is at 25.
  assert.ok(urHead.tick > urLog[urLog.length - 1].tick);
  assert.ok(OW.covers(urHead, urLog));
  const last = urLog[urLog.length - 1];
  assert.ok(!OW.covers({ ...urHead, tick: last.tick - 1 }, urLog), "a tick before the last entry");
  assert.ok(!OW.covers({ ...urHead, length: urLog.length - 1 }, urLog), "a length that isn't the log's");
  assert.ok(!OW.covers(urHead, urLog.slice(0, -1)), "a log cut short");
  assert.ok(OW.covers({ length: 0, last: OW.GENESIS, tick: 0 }, []));
});

test("a signed head with a field its format doesn't have is refused", async () => {
  const key = freshKey(), log = hosted.worlds[0].log;
  assert.equal(await OW.signedBy(await signed(headFor(key, log), key), key.did, HEAD), "ok");
  const extra = await signed({ ...headFor(key, log), note: "more" }, key);
  assert.match(await OW.signedBy(extra, key.did, HEAD), /a field its format doesn't have: "note"/);
  // Fields named as every object's own are fields like any other.
  for (const name of ["__proto__", "toString", "constructor", "hasOwnProperty"]) {
    const odd = await signed(Object.assign(JSON.parse('{"' + name + '": 1}'), headFor(key, log)), key);
    assert.equal(await OW.signedBy(odd, key.did, HEAD), "has a field its format doesn't have: \"" + name + "\"", name);
  }
  assert.equal(OW.shapeProblem(headFor(key, log), "toString"), "a format this page doesn't read");
  const short = headFor(key, log); delete short.tick;
  assert.match(await OW.signedBy(await signed(short, key), key.did, HEAD), /lacks its "tick"/);
  const negative = await signed({ ...headFor(key, log), length: -1 }, key);
  assert.match(await OW.signedBy(negative, key.did, HEAD), /"length" isn't written/);
});

test("a proof with another field, or another purpose, is refused", async () => {
  const key = freshKey(), log = hosted.worlds[0].log;
  const extra = await signed(headFor(key, log), key, { domain: "x" });
  assert.match(await OW.signedBy(extra, key.did, HEAD), /exactly the fields a proof has/);
  const purpose = await signed(headFor(key, log), key, { proofPurpose: "authentication" });
  assert.match(await OW.signedBy(purpose, key.did, HEAD), /time or purpose/);
});

test("a record changed after signing, or signed by another key, is refused", async () => {
  const w = hosted.worlds[1], key = w.log[0].data.world;
  assert.equal(await OW.signedBy({ ...w.head, tick: w.head.tick + 1 }, key, HEAD), "its signature doesn't hold");
  assert.equal(await OW.signedBy(w.head, hosted.worlds[0].log[0].data.world, HEAD), "names another world");
  const other = freshKey();
  const forged = await signed(OW.without({ ...w.head, world: key }, "proof"), other);
  assert.equal(await OW.signedBy(forged, key, HEAD), "signed by another key than the world's");
});

test("a birth record is read field for field", async () => {
  const key = freshKey();
  const base = OW.without({ ...hosted.worlds[1].birth, world: key.did }, "proof");
  assert.equal(await OW.signedBy(await signed(base, key), key.did, BIRTH), "ok");
  const cases = [
    [{ ...base, colour: "green" }, /a field its format doesn't have/],
    [OW.without(base, "template"), /sets dials, but names no template/],
    [{ ...base, name: " \n " }, /"name" isn't written/],
    [{ ...base, name: "a\u0007b" }, /"name" isn't written/],
    [{ ...base, name: "x".repeat(65) }, /"name" isn't written/],
    [{ ...base, founders: [key.did, key.did] }, /"founders" isn't written/],
    [{ ...base, dials: {} }, /"dials" isn't written/],
    [OW.without(base, "time"), /lacks its "time"/],
  ];
  for (const [record, why] of cases) assert.match(await OW.signedBy(await signed(record, key), key.did, BIRTH), why);
  // A number that isn't whole can't be signed the standard way at all.
  assert.match(OW.shapeProblem({ ...base, dials: { branchLength: 1.5 } }, BIRTH), /"dials" isn't written/);
  assert.equal(await OW.signedBy(await signed({ ...base, name: "x".repeat(64) }, key), key.did, BIRTH), "ok");
});

test("a birth record names exactly the dials changed from its template", () => {
  const t = hosted.template, b = hosted.worlds[1].birth, logDials = hosted.worlds[1].log[0].data.dials;
  assert.equal(OW.dialsProblem(b, t, null), null);
  assert.match(OW.dialsProblem({ ...b, dials: { ...b.dials, water: t.parameters.water.value } }, t, null), /template's own value/);
  assert.match(OW.dialsProblem({ ...b, dials: { maxDepth: 13 } }, t, null), /outside the template's range/);
  assert.match(OW.dialsProblem({ ...b, dials: { toString: 1 } }, t, null), /isn't one of the template's dials/);
  assert.match(OW.dialsProblem({ ...b, dials: { maxDepth: 8 } }, t, logDials), /exactly the dials changed/);
  assert.match(OW.dialsProblem({ ...b, dials: { ...b.dials, maxDepth: 9 } }, t, logDials), /aren't the log's/);
});

test("two logs are the same only if every entry is, and as many", () => {
  // Its answers come from the script's own realm: compare them as data.
  const sameLog = (a, b) => { const r = OW.sameLog(a, b); return r === null ? null : { ...r }; };
  const log = hosted.worlds[1].log;
  assert.equal(sameLog(log, copy(log)), null);
  const changed = copy(log); changed[3].data.tips = [];
  assert.deepEqual(sameLog(log, changed), { at: 3 });
  // A grown log that stops sooner, and one that goes on further.
  assert.deepEqual(sameLog(log, log.slice(0, 7)), { at: 7 });
  const longer = [...copy(log), { tick: 99, kind: "more" }];
  assert.deepEqual(sameLog(log, longer), { at: log.length });
  assert.deepEqual(sameLog(longer, log), { at: log.length });
  assert.deepEqual(sameLog(log, "not a log"), { at: 0 });
  // An entry the log format can't write is reported, not thrown.
  const odd = copy(log); odd[2].tick = 0.5;
  assert.match(sameLog(odd, log).why, /whole number/);
});

test("Plant Watch says how a log and its world grown again compare", () => {
  // Its answers come from the script's own realm: compare them as data.
  const row = (a, b) => [...OW.grownAgain(a, b)];
  const log = hosted.worlds[1].log;
  assert.deepEqual(row(log, copy(log)), ["ok",
    "The plant world's own Rust code, compiled to WebAssembly, grows the same " + log.length + " entries here, hash for hash."]);
  const changed = copy(log); changed[3].data.tips = [];
  assert.deepEqual(row(log, changed), ["bad", "The plant world's own code grows another log, from [3]."]);
  assert.deepEqual(row(log, log.slice(0, 7)), ["bad",
    "The plant world's own code grows 7 entries, where this log has " + log.length + "."]);
  const longer = [...copy(log), { tick: 99, kind: "more" }];
  assert.deepEqual(row(log, longer), ["bad",
    "The plant world's own code grows " + longer.length + " entries, where this log has " + log.length + "."]);
  // An answer that isn't a log, and one with an entry no log can hold.
  for (const answer of [{ worlds: [] }, "a log", null, 5]) {
    assert.deepEqual(row(log, answer), ["bad", "Its answer isn't a log."], JSON.stringify(answer));
  }
  const odd = copy(log); odd[2].tick = 0.5;
  assert.match(row(log, odd)[1], /^Its answer can't be compared: .*whole number/);
});

test("a log changed anywhere breaks its chain", async () => {
  const log = copy(urLog);
  log[40].data.text = "changed";
  assert.match(await OW.chainProblem(log), /^\[40\]: its hash doesn't match/);
  const cut = copy(urLog).slice(1);
  assert.match(await OW.chainProblem(cut), /^\[0\]: doesn't follow/);
  // JSON.parse keeps "__proto__" as a field, and so does the hash.
  const proto = copy(hosted.worlds[0].log);
  proto[2] = Object.assign(JSON.parse('{"__proto__": "x"}'), proto[2]);
  assert.match(await OW.chainProblem(proto), /^\[2\]: its hash doesn't match/);
});

test("what it hands out can't change how it checks", () => {
  assert.ok(Object.isFrozen(OW));
  assert.throws(() => { "use strict"; OW.signedBy = async () => "ok"; }, TypeError);
  // Only functions and a string: no pattern or table the checks use
  // inside is reachable from outside.
  for (const [name, v] of Object.entries(OW)) {
    assert.ok(typeof v === "function" || typeof v === "string", name);
  }
});
