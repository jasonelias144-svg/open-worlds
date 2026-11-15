// web/lib/wasi.js
// Runs a WebAssembly command built for WASI (wasm32-wasip1), such as the
// plant world's (rust/plant-wasi), in the page: one request on standard
// input, the answer on standard output. It gives the command exactly the
// five WASI calls the plant world uses, and nothing else: reading standard
// input, writing standard output and error, an empty environment, and
// exit. No clock, no randomness, no files: a command that asks for any
// other call isn't run. A classic script, like checks.js; it defines one
// name, OpenWorldsWasi, and nothing it holds can be changed from outside.
"use strict";
const OpenWorldsWasi = (function () {
  const MODULE = "wasi_snapshot_preview1";
  const CALLS = ["environ_get", "environ_sizes_get", "fd_read", "fd_write", "proc_exit"];
  const EBADF = 8;

  // The calls a compiled command asks for that this file doesn't give.
  function missing(module) {
    return WebAssembly.Module.imports(module)
      .filter(i => i.module !== MODULE || !CALLS.includes(i.name) || i.kind !== "function")
      .map(i => i.module + "." + i.name);
  }

  // Runs `module` (a compiled WebAssembly.Module) once, with `input` (text)
  // as its standard input: { code, stdout, stderr }, the exit code and what
  // it wrote, as text.
  async function run(module, input) {
    const extra = missing(module);
    if (extra.length) throw new Error("the command asks for calls this page doesn't give: " + extra.join(", "));
    const stdin = new TextEncoder().encode(input);
    let read = 0, memory = null, code = null;
    const out = [], err = [];
    const EXIT = {};
    const view = () => new DataView(memory.buffer);
    // Each of `count` buffers is a pointer and a length, 8 bytes in all.
    const buffers = (iovs, count) => Array.from({ length: count }, (_, i) =>
      [view().getUint32(iovs + i * 8, true), view().getUint32(iovs + i * 8 + 4, true)]);
    const calls = {
      environ_sizes_get(countAt, sizeAt) { view().setUint32(countAt, 0, true); view().setUint32(sizeAt, 0, true); return 0; },
      environ_get() { return 0; },
      fd_read(fd, iovs, count, readAt) {
        if (fd !== 0) return EBADF;
        let n = 0;
        for (const [at, len] of buffers(iovs, count)) {
          const chunk = stdin.subarray(read, read + len);
          new Uint8Array(memory.buffer, at, chunk.length).set(chunk);
          read += chunk.length; n += chunk.length;
          if (chunk.length < len) break;
        }
        view().setUint32(readAt, n, true);
        return 0;
      },
      fd_write(fd, iovs, count, writtenAt) {
        if (fd !== 1 && fd !== 2) return EBADF;
        let n = 0;
        for (const [at, len] of buffers(iovs, count)) {
          (fd === 1 ? out : err).push(new Uint8Array(memory.buffer, at, len).slice());
          n += len;
        }
        view().setUint32(writtenAt, n, true);
        return 0;
      },
      proc_exit(c) { code = c; throw EXIT; },
    };
    const instance = await WebAssembly.instantiate(module, { [MODULE]: calls });
    memory = instance.exports.memory;
    if (!(memory instanceof WebAssembly.Memory) || typeof instance.exports._start !== "function") {
      throw new Error("not a WASI command: it has no memory or no _start");
    }
    try { instance.exports._start(); if (code === null) code = 0; }
    catch (e) { if (e !== EXIT) throw e; }
    const text = parts => {
      const all = new Uint8Array(parts.reduce((n, p) => n + p.length, 0));
      let at = 0;
      for (const p of parts) { all.set(p, at); at += p.length; }
      return new TextDecoder().decode(all);
    };
    return { code, stdout: text(out), stderr: text(err) };
  }

  return Object.freeze({ CALLS: Object.freeze(CALLS.slice()), missing, run });
})();
