// web/lib/checks.js
// The checks the web app's pages share: a log's chain of hashes, and
// records signed the standard way (eddsa-jcs-2022), read field for field
// as records-v1 (schemas/records-v1.schema.json) reads them. A classic
// script, so a page served from disk can load it too; it defines one name,
// OpenWorlds, and nothing it holds can be changed from outside.
"use strict";
const OpenWorlds = (function () {
  // ---- The common log format: each entry's hash is SHA-256 of the entry
  // without its hash, written as Python's json.dumps(sort_keys=True,
  // separators=(",", ":")) writes it, ASCII only (rust/world-log).
  const GENESIS = "0".repeat(64);
  const HASH = /^[0-9a-f]{64}$/;

  function pyString(s) {
    let out = '"';
    for (const ch of s) {
      const c = ch.codePointAt(0);
      if (ch === '"') out += '\\"';
      else if (ch === "\\") out += "\\\\";
      else if (ch === "\b") out += "\\b";
      else if (ch === "\f") out += "\\f";
      else if (ch === "\n") out += "\\n";
      else if (ch === "\r") out += "\\r";
      else if (ch === "\t") out += "\\t";
      else if (c < 0x20 || c > 0x7e) {
        const units = c > 0xffff ? [0xd800 + ((c - 0x10000) >> 10), 0xdc00 + ((c - 0x10000) & 0x3ff)] : [c];
        out += units.map(u => "\\u" + u.toString(16).padStart(4, "0")).join("");
      } else out += ch;
    }
    return out + '"';
  }
  function pyJson(v) {
    if (v === null) return "null";
    if (v === true) return "true";
    if (v === false) return "false";
    if (typeof v === "number") {
      if (!Number.isSafeInteger(v)) throw new Error("a number that isn't a whole number within 2^53");
      if (Object.is(v, -0)) throw new Error("-0, which Rust reads as a float");
      return String(v);
    }
    if (typeof v === "string") return pyString(v);
    if (Array.isArray(v)) return "[" + v.map(pyJson).join(",") + "]";
    const keys = Object.keys(v).sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
    return "{" + keys.map(k => pyString(k) + ":" + pyJson(v[k])).join(",") + "}";
  }
  // RFC 8785 for the records this project signs: whole numbers, text,
  // and keys sorted by UTF-16 code units, as JSON.stringify writes them.
  function jcs(v) {
    if (v === null || typeof v !== "object") {
      if (typeof v === "number" && !Number.isSafeInteger(v)) throw new Error("a number outside the three rules");
      return JSON.stringify(v);
    }
    if (Array.isArray(v)) return "[" + v.map(jcs).join(",") + "]";
    const keys = Object.keys(v).sort();
    return "{" + keys.map(k => JSON.stringify(k) + ":" + jcs(v[k])).join(",") + "}";
  }
  // A copy of an object without one key. JSON.parse keeps a "__proto__"
  // key as an ordinary field, and so does this copy (Object.assign would
  // drop it), so the page hashes and compares what Python and Rust do.
  const without = (o, key) => Object.fromEntries(Object.entries(o).filter(([k]) => k !== key));
  async function sha256(bytes) { return new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)); }
  const text = s => new TextEncoder().encode(s);
  const hex = b => Array.from(b, x => x.toString(16).padStart(2, "0")).join("");
  // A record's hash, as records-v1 names records: SHA-256 of its RFC 8785 form.
  async function recordHash(v) { return hex(await sha256(text(jcs(v)))); }

  async function chainProblem(log) {
    if (!Array.isArray(log)) return "not a list of entries";
    let prev = GENESIS;
    for (let i = 0; i < log.length; i++) {
      const e = log[i];
      if (!e || typeof e !== "object" || Array.isArray(e) || typeof e.hash !== "string") return "[" + i + "]: not an entry with a hash";
      const body = without(e, "hash");
      if (body.prev !== prev) return "[" + i + "]: doesn't follow the entry before it";
      if (hex(await sha256(text(pyJson(body)))) !== e.hash) return "[" + i + "]: its hash doesn't match what it says";
      prev = e.hash;
    }
    return null;
  }

  // ---- Keys: did:key, Ed25519, in its one written form.
  const B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";
  function base58(s) {
    let n = 0n;
    for (const ch of s) { const i = B58.indexOf(ch); if (i < 0) throw new Error("not base58"); n = n * 58n + BigInt(i); }
    const out = [];
    while (n > 0n) { out.unshift(Number(n % 256n)); n /= 256n; }
    for (const ch of s) { if (ch === "1") out.unshift(0); else break; }
    return new Uint8Array(out);
  }
  function base58encode(bytes) {
    let n = 0n;
    for (const x of bytes) n = n * 256n + BigInt(x);
    let out = "";
    while (n > 0n) { out = B58[Number(n % 58n)] + out; n /= 58n; }
    for (const x of bytes) { if (x === 0) out = "1" + out; else break; }
    return out;
  }
  function publicKey(did) {
    if (typeof did !== "string" || !did.startsWith("did:key:z")) throw new Error("not a did:key");
    const b = base58(did.slice(9));
    if (b.length !== 34 || b[0] !== 0xed || b[1] !== 0x01) throw new Error("not an Ed25519 key");
    if (base58encode(b) !== did.slice(9)) throw new Error("not the key's one written form");
    return b.slice(2);
  }
  const isKey = v => { try { publicKey(v); return true; } catch (e) { return false; } };

  // ---- Records, field for field as records-v1 has them: each format's
  // required fields, the ones it may have, and what each must be. A record
  // with any other field is refused, as the schema refuses it, even when
  // its signature holds.
  const TIME = /^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$/;
  const isText = v => typeof v === "string";
  const isWhole = v => Number.isSafeInteger(v) && v >= 0;
  const isHash = v => typeof v === "string" && HASH.test(v);
  // Text as records-v1 has it: not empty, not only spaces or line breaks,
  // and no control characters but tab and line breaks.
  const SPACES = /^[ \t\n\r\u000b\u000c\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000\ufeff]*$/;
  const CONTROL = /[\u0000-\u0008\u000e-\u001f\u007f-\u0084\u0086-\u009f]/;
  const isName = v => typeof v === "string" && !SPACES.test(v) && !CONTROL.test(v) && Array.from(v).length <= 64;
  const isPlain = v => v !== null && typeof v === "object" && !Array.isArray(v);
  // Own fields only: a field named "toString" or "__proto__" is a field
  // like any other, never something every object inherits.
  const has = (o, k) => Object.prototype.hasOwnProperty.call(o, k);
  const DIAL = /^[a-z][A-Za-z0-9]*$/;
  const FORMATS = {
    "open-worlds/log-head/v1": {
      required: { format: isText, world: isKey, length: isWhole, last: isHash, tick: isWhole, proof: isPlain },
      optional: {},
    },
    "open-worlds/world-birth/v1": {
      required: {
        format: isText, world: isKey, name: isName, law: isHash, time: v => isText(v) && TIME.test(v), proof: isPlain,
        founders: v => Array.isArray(v) && v.every(isKey) && new Set(v).size === v.length,
      },
      optional: {
        template: isHash,
        forkedFrom: v => isPlain(v) && Object.keys(v).sort().join(",") === "log,tick,world" && isKey(v.world) && isWhole(v.tick) && isHash(v.log),
        dials: v => isPlain(v) && Object.keys(v).length >= 1 && Object.entries(v).every(([k, x]) => DIAL.test(k) && k.length <= 64 && Number.isSafeInteger(x)),
      },
    },
  };
  const PROOF_FIELDS = "created,cryptosuite,proofPurpose,proofValue,type,verificationMethod";
  // Why `record` isn't a record of `format` as records-v1 writes one, or null.
  function shapeProblem(record, format) {
    const f = has(FORMATS, format) ? FORMATS[format] : null;
    if (!f) return "a format this page doesn't read";
    if (!isPlain(record) || record.format !== format) return "not a record of the format " + format;
    for (const k of Object.keys(record)) {
      const test = has(f.required, k) ? f.required[k] : has(f.optional, k) ? f.optional[k] : null;
      if (!test) return "has a field its format doesn't have: " + JSON.stringify(k);
      if (!test(record[k])) return "its " + JSON.stringify(k) + " isn't written as its format requires";
    }
    for (const k of Object.keys(f.required)) if (!has(record, k)) return "lacks its " + JSON.stringify(k);
    if (format === "open-worlds/world-birth/v1" && has(record, "dials") && !has(record, "template")) return "sets dials, but names no template";
    return null;
  }

  // Whether `record` is a record of `format`, signed by `signer` (a
  // did:key): "ok", or why not, or "unsupported" where this browser can't
  // check Ed25519. eddsa-jcs-2022, as formats/proof.py verifies it.
  async function signedBy(record, signer, format) {
    try {
      const shape = shapeProblem(record, format);
      if (shape) return shape;
      if (record.world !== signer) return "names another world";
      const proof = record.proof;
      if (Object.keys(proof).sort().join(",") !== PROOF_FIELDS) return "its proof doesn't have exactly the fields a proof has";
      if (proof.type !== "DataIntegrityProof" || proof.cryptosuite !== "eddsa-jcs-2022") return "not an eddsa-jcs-2022 proof";
      if (proof.verificationMethod !== signer + "#" + signer.slice(8)) return "signed by another key than the world's";
      if (typeof proof.created !== "string" || !TIME.test(proof.created) || proof.proofPurpose !== "assertionMethod") return "its proof's time or purpose isn't written as required";
      const unsecured = without(record, "proof");
      const options = without(proof, "proofValue");
      if (typeof proof.proofValue !== "string" || proof.proofValue[0] !== "z") return "its signature isn't base58";
      const signature = base58(proof.proofValue.slice(1));
      if (signature.length !== 64) return "its signature isn't 64 bytes";
      const data = new Uint8Array(64);
      data.set(await sha256(text(jcs(options))), 0);
      data.set(await sha256(text(jcs(unsecured))), 32);
      let key;
      try { key = await crypto.subtle.importKey("raw", publicKey(signer), { name: "Ed25519" }, false, ["verify"]); }
      catch (e) { return "unsupported"; }
      return (await crypto.subtle.verify({ name: "Ed25519" }, key, signature, data)) ? "ok" : "its signature doesn't hold";
    } catch (e) { return String(e.message || e); }
  }

  // Whether a head covers all of `log` as given: its length and last hash
  // are the log's, and its tick isn't before the last entry's. A head's
  // tick says only that the world was at least that far along, since ticks
  // can pass with nothing written (rust/ur-world, `head_coverage`).
  function covers(head, log) {
    const last = log[log.length - 1];
    if (!last) return head.length === 0 && head.last === GENESIS;
    return head.length === log.length && head.last === last.hash && Number.isSafeInteger(last.tick) && head.tick >= last.tick;
  }

  // The dials a birth record sets, against its template's parameters: why
  // they aren't the template's own dials, each within its range and
  // changed from the template's value, or null. `dials` is what the world
  // was made with, where the page holds it (its log's first entry): then
  // the birth record must name exactly the dials changed from the template.
  function dialsProblem(birth, template, dials) {
    const params = template && isPlain(template.parameters) ? template.parameters : null;
    if (!params) return "the template given with it has no parameters";
    const set = birth.dials || {};
    for (const [k, v] of Object.entries(set)) {
      const p = has(params, k) ? params[k] : null;
      if (!isPlain(p)) return "sets " + k + ", which isn't one of the template's dials";
      if (v < p.min || v > p.max) return "sets " + k + " to " + v + ", outside the template's range";
      if (v === p.value) return "names " + k + " as set, but at the template's own value";
    }
    if (dials) {
      for (const k of Object.keys(dials)) {
        const p = has(params, k) ? params[k] : null;
        if (!isPlain(p)) return "its log has a dial, " + k + ", the template doesn't have";
        if ((dials[k] !== p.value) !== has(set, k)) return "it doesn't name exactly the dials changed from the template";
        if (has(set, k) && set[k] !== dials[k]) return "its dials aren't the log's";
      }
      if (Object.keys(set).some(k => !has(dials, k))) return "its dials aren't the log's";
    }
    return null;
  }

  return Object.freeze({
    GENESIS, HASH, TIME, pyJson, jcs, without, sha256, text, hex, recordHash,
    chainProblem, base58, base58encode, publicKey, isKey, shapeProblem,
    signedBy, covers, dialsProblem,
  });
})();
