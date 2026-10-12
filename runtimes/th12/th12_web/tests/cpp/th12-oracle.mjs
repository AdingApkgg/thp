// TH12 original-executable oracle harness (development only).
//
// Addresses below were located in `reference/th12-decomp` (Ghidra delink corpus,
// one file per function named `<symbol>_<address>.c`) and confirmed by reading the
// recovered C. They are TH12's own entry points and must never be reused from TH11.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { NativeMachine } from '../../scripts/native/machine.mjs';

export const root = fileURLToPath(new URL('../../', import.meta.url));
export const target = JSON.parse(readFileSync(resolve(root, 'target.json'), 'utf8'));
export const sha = b => createHash('sha256').update(b).digest('hex');

/** TH12 CRT entry points (statically linked MSVC CRT inside th12.exe). */
export const TH12_CRT = {
  malloc: 0x0046d04a, // _malloc_0046d04a.c
  free: 0x0046c941,   // _free_0046c941.c
  memcpy: 0x0047a330, // _memcpy_0047a330.c
};

/** TH12 gameplay RNG. Same xorshift-rotl2 family as TH11, different addresses. */
export const TH12_RNG = {
  next16: 0x004643d0, // FUN_004643d0_004643d0.c
  next32: 0x00464440, // FUN_00464440_00464440.c
};

function executablePath() {
  return /^[A-Za-z]:[\\/]/.test(target.executable)
    ? target.executable
    : resolve(root, target.executable);
}

export async function th12Oracle() {
  const bytes = readFileSync(executablePath());
  if (sha(bytes) !== target.sha256) throw Error(`TH12 target hash mismatch (${target.sha256})`);

  const m = await NativeMachine.create(bytes);
  m.resetThreadFPU();

  // The retail CRT heap is initialised by the skipped CRT startup, so route heap
  // traffic to the oracle's own allocator exactly like the TH11 harness does.
  m.replace(TH12_CRT.malloc, 'malloc', () => m.allocate(m.u32(m.reg('ESP') + 4)));
  m.replace(TH12_CRT.free, 'free', () => 0);
  m.replace(TH12_CRT.memcpy, 'memcpy', () => {
    const dst = m.u32(m.reg('ESP') + 4);
    const src = m.u32(m.reg('ESP') + 8);
    const n = m.u32(m.reg('ESP') + 12);
    m.write(dst, m.bytes(src, n));
    return dst;
  });

  m.onImport = e => {
    if (e.handler) m.ret(e.handler(), e.argc);
    else throw Error(`Unimplemented import ${e.dll}!${e.name}`);
  };
  return m;
}

/** Write an 8-byte TH12 Rng (`u16 seed, u16 reserved, u32 calls`) into oracle memory. */
export function writeRng(m, address, seed, calls = 0) {
  const b = Buffer.alloc(8);
  b.writeUInt16LE(seed & 0xffff, 0);
  b.writeUInt32LE(calls >>> 0, 4);
  m.write(address, b);
}
