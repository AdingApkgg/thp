// Find a title's replay-container parameters by demanding an exact decode, not a plausible one.
//
// A replay body is a cipher pass (or two) followed by an LZSS stream whose length the header
// declares at +0x20. The success criterion is exact: the stream must terminate having produced
// precisely `unpacked` bytes, and the decoded header must satisfy the format's invariants
// (stage count 1..7, character/type/difficulty in range). Parameter sets that satisfy that for
// every attract demo a title ships are the title's; one demo alone is not enough.
//
// The candidate pool is not a guess: it holds the pairs read out of the engine's own loaders
// (the two replay pairs TH11/TH12 used) and the archive cipher tables thtk documents per version,
// plus a key sweep around them, so a title whose replay keys were never read still has a chance
// to fall out of the search with proof attached.
//
//   node tools/th-replay-keys.mjs --dir runtimes/th13/th13_web/artifacts/cpp/th13-data
import { readFileSync, existsSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';

const argOf = n => { const at = process.argv.indexOf('--' + n); return at < 0 ? null : process.argv[at + 1]; };
const dir = resolve(argOf('dir') || 'runtimes/th13/th13_web/artifacts/cpp/th13-data');

function resource_crypt(input, size, p, encrypt) {
  const out = new Uint8Array(size);
  let key = p.key;
  const mod = size % p.block;
  const untouched = (mod < Math.floor(p.block / 4) ? mod : 0) + (size & 1);
  let remaining = size - untouched, limit = p.limit ?? size, cursor = 0;
  while (remaining > 0 && limit > 0) {
    const block = Math.min(p.block, remaining);
    let linear = 0;
    for (let parity = 1; parity <= 2; parity++) {
      for (let pos = block - parity; pos >= 0; pos -= 2) {
        if (encrypt) out[cursor + linear] = input[cursor + pos] ^ key;
        else out[cursor + pos] = input[cursor + linear] ^ key;
        key = (key + p.step) & 0xff;
        linear++;
      }
    }
    cursor += block; remaining -= block; limit -= block;
  }
  if (cursor < size) out.set(input.subarray(cursor, size), cursor);
  return out;
}

function lzss(input, size, capacity, offsetBits, lengthBits, dictSize) {
  const output = new Uint8Array(capacity);
  const dict = new Uint8Array(dictSize);
  let cursor = 0, written = 0, head = 1, mask = 0x80, byte = 0;
  const bit = () => {
    if (mask === 0x80) byte = cursor < size ? input[cursor++] : 0;
    const r = (byte & mask) ? 1 : 0;
    mask >>= 1; if (!mask) mask = 0x80;
    return r;
  };
  const bits = n => { let v = 0; while (n--) v = (v << 1) | bit(); return v; };
  const put = v => { output[written++] = v; dict[head] = v; head = (head + 1) & (dictSize - 1); };
  for (;;) {
    if (bit()) { if (written === capacity) return { written, complete: false, output }; put(bits(8)); }
    else {
      const offset = bits(offsetBits);
      if (!offset) return { written, complete: true, output };
      const length = bits(lengthBits) + 3;
      if (length > capacity - written) return { written, complete: false, output };
      for (let i = 0; i < length; i++) put(dict[(offset + i) & (dictSize - 1)]);
    }
  }
}

const ARCHIVE = {
  th95: [[0x1b, 0x37, 0x40], [0x51, 0xe9, 0x40], [0xc1, 0x51, 0x80], [0x03, 0x19, 0x400], [0xab, 0xcd, 0x200], [0x12, 0x34, 0x80], [0x35, 0x97, 0x80], [0x99, 0x37, 0x400]],
  th12: [[0x1b, 0x73, 0x40], [0x51, 0x9e, 0x40], [0xc1, 0x15, 0x400], [0x03, 0x91, 0x80], [0xab, 0xdc, 0x80], [0x12, 0x43, 0x200], [0x35, 0x79, 0x400], [0x99, 0x7d, 0x80]],
  th13: [[0x1b, 0x73, 0x100], [0x12, 0x43, 0x200], [0x35, 0x79, 0x400], [0x03, 0x91, 0x80], [0xab, 0xdc, 0x80], [0x51, 0x9e, 0x100], [0xc1, 0x15, 0x400], [0x99, 0x7d, 0x80]],
  th14: [[0x1b, 0x73, 0x100], [0x12, 0x43, 0x200], [0x35, 0x79, 0x400], [0x03, 0x91, 0x80], [0xab, 0xdc, 0x80], [0x51, 0x9e, 0x100], [0xc1, 0x15, 0x400], [0x99, 0x7d, 0x80]],
};
// The two replay pairs the engine's loaders used (TH11 then TH12), then the archive tables.
// TH13's two pairs were read out of th13.exe with `tools/th-replay-keys-exe.py`, whose first
// check is that it finds TH12's known pair in th12.exe: at `mov al,0x5c / push 0xe1 / push
// 0x100` and `mov al,0x7d / push 0x3a / push 0x100`, where TH12 has 0x5e/0xe1/0x800 and
// 0x7d/0x3a/0x40. The 0x400 pushes next to them are the other cipher call in the same
// routine, so both block sizes are candidates here and the decode decides between them.
const CRYPT_POOL = [[0xaa, 0xe1, 0x800], [0x3d, 0x7a, 0x40], [0x5e, 0xe1, 0x800], [0x7d, 0x3a, 0x40],
                    [0x5c, 0xe1, 0x100], [0x5c, 0xe1, 0x400], [0x7d, 0x3a, 0x100], [0x7d, 0x3a, 0x400]];
for (const rows of Object.values(ARCHIVE)) CRYPT_POOL.push(...rows);
// A sweep with the same block sizes, for the case the keys were never read out of a loader.
for (let key = 0; key < 256; key += 1) {
  if (key % 17 === 0) { CRYPT_POOL.push([key, 0xe1, 0x800]); CRYPT_POOL.push([key, 0x7a, 0x40]); }
}
const LZSS_VARIANTS = [[13, 4, 8192], [12, 5, 8192], [14, 4, 16384], [13, 4, 16384], [11, 6, 4096], [15, 4, 32768]];
const PACKED_FIELDS = [['+0x1c', 0x1c], ['+0x0c', 0x0c], ['size-0x24', null]];

const VERBOSE = process.argv.includes('--verbose');
const files = readdirSync(dir).filter(n => /^demo\d\.rpy$/.test(n) || /^\w+\.rpy$/.test(n)).sort()
  .map(n => [n, resolve(dir, n)]).filter(([, p]) => existsSync(p));
if (!files.length) { console.log(`  no .rpy files in ${dir}`); process.exit(0); }
console.log(`  ${files.length} replay(s) in ${dir}: ${files.map(([n]) => n).join(' ')}`);

// Every candidate that fills the declared size. The header invariants are *TH12's offsets*, so
// they are reported per candidate rather than required: a title can decode perfectly and still
// disagree about where its decoded header keeps the stage count, and that is a separate
// measurement from the ciphers.
const perFile = files.map(([name, path]) => {
  const data = readFileSync(path);
  const unpacked = data.readUInt32LE(0x20);
  const good = new Map();
  let best = { written: 0, complete: false, params: null };
  for (const [flabel, foff] of PACKED_FIELDS) {
    const packed = foff === null ? data.length - 0x24 : data.readUInt32LE(foff);
    if (!packed || packed > data.length - 0x24) continue;
    const body = data.subarray(0x24, 0x24 + packed);
    const stages1 = [['none', null], ...CRYPT_POOL.map((p, i) => [`p${i}`, p])].map(([l1, p1]) => {
      const bytes = p1 ? resource_crypt(body, packed, { key: p1[0], step: p1[1], block: p1[2] }, false) : body;
      return { l1, p1, bytes };
    });
    for (const { l1, p1, bytes: stage1 } of stages1) {
      for (const [l2, p2] of [['none', null], ...CRYPT_POOL.map((p, i) => [`p${i}`, p])]) {
        const stage2 = p2 ? resource_crypt(stage1, packed, { key: p2[0], step: p2[1], block: p2[2] }, false) : stage1;
        for (const [ob, lb, ds] of LZSS_VARIANTS) {
          const r = lzss(stage2, packed, unpacked, ob, lb, ds);
          if (r.written > best.written)
            best = { written: r.written, complete: r.complete,
                     params: [l1, p1, l2, p2, ob, lb, ds, flabel] };
          // A stream that fills the declared size on its last literal ends without the
          // zero-offset marker, so a full decode counts even when it did not terminate.
          if (r.written !== unpacked) continue;
          const h = new DataView(r.output.buffer, r.output.byteOffset, r.output.byteLength);
          const n = h.getUint32(0x58, true), a = h.getUint32(0x5c, true),
                b = h.getUint32(0x60, true), c = h.getUint32(0x64, true);
          const hdrOk = !(n < 1 || n > 7 || a > 1 || b > 2 || c > 4);
          const key = JSON.stringify([flabel, l1, p1, l2, p2, ob, lb, ds]);
          good.set(key, { hdrOk, output: r.output, n, selection: [a, b, c] });
        }
      }
    }
  }
  console.log(`  ${name}: ${good.size} parameter set(s) fill ${unpacked} bytes; best wrote ${best.written}${best.complete ? ' (terminated)' : ''}`);
  if (VERBOSE) for (const [key, value] of good) console.log(`      ${value.hdrOk ? 'header ok   ' : 'header off  '} ${key}`);
  return { name, good };
});

const all = files.length;
const tally = new Map();
for (const { good } of perFile) for (const key of good.keys()) tally.set(key, (tally.get(key) || 0) + 1);
const winners = [...tally.entries()].filter(([, n]) => n === all).map(([k]) => JSON.parse(k));
console.log(`  ${winners.length} parameter set(s) decode all ${all} replays`);
for (const [flabel, l1, p1, l2, p2, ob, lb, ds] of winners.slice(0, 8)) {
  const okCount = perFile.filter(({ good }) => good.get(JSON.stringify([flabel, l1, p1, l2, p2, ob, lb, ds]))?.hdrOk).length;
  console.log(`    packed=${flabel} pass1=${l1}${p1 ? '=' + p1 : ''} pass2=${l2}${p2 ? '=' + p2 : ''} lzss=(${ob},${lb},${ds}) TH12-header-invariants ${okCount}/${all}`);
}
const nameOfSet = ([flabel, l1, p1, l2, p2, ob, lb, ds]) => JSON.stringify([flabel, l1, p1, l2, p2, ob, lb, ds]);
const dumpAt = process.argv.indexOf('--dump');
if (dumpAt >= 0 && winners.length) {
  const [flabel, l1, p1, l2, p2, ob, lb, ds] = winners[0];
  const name = argOf('dump') || files[0][0];
  const entry = perFile.find(f => f.name === name)?.good.get(JSON.stringify([flabel, l1, p1, l2, p2, ob, lb, ds]));
  if (!entry) { console.log(`    ${name} has no decode from the first winning set`); }
  else {
    const bytes = entry.output.subarray(0, 0x90), words = [];
    for (let at = 0; at + 4 <= bytes.length; at += 4) words.push(`+${at.toString(16)}:${new DataView(bytes.buffer, bytes.byteOffset + at, 4).getUint32(0, true)}`);
    console.log(`    ${name} decoded head: ${[...bytes].map(b => b.toString(16).padStart(2, '0')).join(' ')}`);
    console.log(`    as dwords: ${words.join(' ')}`);
  }
}

// The stage list's layout is a measurement of its own, and the standard is the same: a pair of
// offsets has to satisfy the parse in Replay.cpp for **every** replay of the title, the final
// `offset == unpacked` included. TH12's pair (0x70, 0xA0) is the instrument's control.
if (process.argv.includes('--layout')) {
  // The selection bounds are the title's as well: TH13 has four characters, TH12 two.
  const charsMax = Number(argOf('chars') ?? 1);
  const parseFor = (out, fh, sh) => {
    const view = new DataView(out.buffer, out.byteOffset, out.byteLength);
    const n = view.getUint32(0x58, true);
    if (!n || n > 7 || view.getUint32(0x5c, true) > charsMax ||
        view.getUint32(0x60, true) > 2 || view.getUint32(0x64, true) > 4) return 'selection';
    let offset = fh;
    const seen = new Set();
    for (let i = 0; i < n; ++i) {
      if (offset > out.length || out.length - offset < sh) return 'truncated stage';
      const st = view.getUint16(offset, true), frames = view.getUint32(offset + 4, true),
            payload = view.getUint32(offset + 8, true);
      if (st < 1 || st > 7 || seen.has(st)) return 'stage number';
      if (payload > out.length - offset - sh || frames > payload / 6) return 'inputs';
      const fps = frames > 1 ? 1 + Math.floor((frames - 2) / 30) : 0;
      if (payload - frames * 6 < fps) return 'frame rates';
      seen.add(st);
      offset += sh + payload;
    }
    return offset === out.length ? 'ok' : `left ${out.length - offset} bytes`;
  };
  const pairArg = argOf('pair');
  if (pairArg) {
    const [fh, sh] = pairArg.split(',').map(v => parseInt(v, 16));
    for (const { name, good } of perFile) {
      const rows = [];
      for (const set of winners) {
        const entry = good.get(nameOfSet(set));
        rows.push(entry ? parseFor(entry.output, fh, sh) : 'no decode');
      }
      console.log(`    ${name} at (0x${fh.toString(16)}, 0x${sh.toString(16)}): ${rows.join(' / ')}`);
    }
  }
  const lines = [], perFileOut = new Map(perFile.map(f => [f.name, []]));
  for (const set of winners) {
    for (let fh = 0x58; fh <= 0x88; fh += 4) {
      for (let sh = 0x40; sh <= 0x140; sh += 4) {
        let ok = 0;
        let reason = 'ok';
        for (const { name, good } of perFile) {
          const entry = good.get(nameOfSet(set));
          if (!entry) { reason = 'no decode'; break; }
          const verdict = parseFor(entry.output, fh, sh);
          if (verdict === 'ok') { ok += 1; perFileOut.get(name).push([fh, sh, set]); }
          else { reason = `${name}: ${verdict}`; }
        }
        if (ok === all) lines.push(`    file header 0x${fh.toString(16)} stage header 0x${sh.toString(16)} satisfies all ${all} replays (${set[0]} pass1=${set[2]} pass2=${set[4]})`);
        else if (fh === 0x70 && sh === 0xa0) lines.push(`    control (0x70, 0xA0): ${ok}/${all} (${reason})`);
      }
    }
  }
  console.log(`  layout scan: ${lines.filter(l => !l.includes('control')).length} pair(s) satisfy every replay`);
  for (const line of lines.slice(0, 12)) console.log(line);
  for (const [name, pairs] of perFileOut) {
    const unique = [...new Set(pairs.map(([fh, sh]) => `0x${fh.toString(16)}/0x${sh.toString(16)}`))];
    console.log(`    ${name}: ${unique.length} pair(s) parse this replay alone, e.g. ${unique.slice(0, 6).join(' ')}`);
  }
}
