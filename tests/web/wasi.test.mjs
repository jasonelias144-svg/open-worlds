// tests/web/wasi.test.mjs
// The plant world's own Rust code, built as a WebAssembly command
// (rust/plant-wasi), run through the page's WASI shim (web/lib/wasi.js):
// it grows exactly the shared vectors' logs. CI builds the command first:
//   cd rust && cargo build --locked --release -p plant-wasi --target wasm32-wasip1
// PLANT_WASI names another build, if it is elsewhere.
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, existsSync } from "node:fs";
import vm from "node:vm";

const root = new URL("../../", import.meta.url);
const read = path => readFileSync(new URL(path, root), "utf8");
const built = process.env.PLANT_WASI
  ? new URL(process.env.PLANT_WASI, `file://${process.cwd()}/`)
  : new URL("rust/target/wasm32-wasip1/release/plant-wasi.wasm", root);

const context = vm.createContext({ WebAssembly, TextEncoder, TextDecoder, Uint8Array, DataView });
const WASI = vm.runInContext(read("web/lib/wasi.js") + "\n;OpenWorldsWasi", context);
const plants = JSON.parse(read("vectors/plant-world.json"));

assert.ok(existsSync(built), "build the command first: " + built.pathname);
const module = await WebAssembly.compile(readFileSync(built));
const request = (world, ticks = 100) => {
  const first = world.log[0].data;
  return JSON.stringify({ key: first.world, template: first.template, dials: first.dials, pot: first.pot, ticks });
};

test("it asks for the five calls the shim gives, and no clock or randomness", () => {
  assert.deepEqual(WASI.missing(module), []);
  const asked = WebAssembly.Module.imports(module).map(i => i.name).sort();
  assert.deepEqual(asked, [...WASI.CALLS].sort());
});

test("every world in the vectors grows the same log", async () => {
  for (const world of plants.worlds) {
    const r = await WASI.run(module, request(world));
    assert.equal(r.code, 0, world.name + ": " + r.stderr);
    assert.deepEqual(JSON.parse(r.stdout), world.log, world.name);
  }
});

test("the same request gives the same bytes", async () => {
  const world = plants.worlds[1];
  const a = await WASI.run(module, request(world)), b = await WASI.run(module, request(world));
  assert.equal(a.stdout, b.stdout);
  assert.ok(a.stdout.length > 1000);
});

test("a refused request exits with 1 and says why", async () => {
  const r = await WASI.run(module, JSON.stringify({ key: "did:key:nope", template: "x", dials: {}, pot: null, ticks: 1 }));
  assert.equal(r.code, 1);
  assert.equal(r.stdout, "");
  assert.match(r.stderr, /dials must be exactly/);
  const notJson = await WASI.run(module, "grow, please");
  assert.equal(notJson.code, 1);
  assert.match(notJson.stderr, /isn't JSON/);
});

test("a command that asks for anything more isn't run", async () => {
  // A module that imports a clock, which the shim doesn't give.
  const clock = new Uint8Array([
    0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00, // magic, version
    0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7f, // type: () -> i32
    0x02, 0x25, 0x01, // the import section: one import, 37 bytes
    0x16, ...new TextEncoder().encode("wasi_snapshot_preview1"),
    0x0a, ...new TextEncoder().encode("clock_time"), 0x00, 0x00,
  ]);
  const m = await WebAssembly.compile(clock);
  assert.deepEqual(WASI.missing(m), ["wasi_snapshot_preview1.clock_time"]);
  await assert.rejects(WASI.run(m, ""), /doesn't give: wasi_snapshot_preview1.clock_time/);
});
