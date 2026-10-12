// TH12 original-executable probe.
//
// Development-only: loads H:/Games/th/12/th12.exe into the Unicorn x86 oracle,
// maps it exactly like the retail loader would, and reports what the oracle can
// see (PE sections, imports, entry point) plus the original CRT entry points we
// must stub before any game function can be called.
//
// This does not run game logic yet and is never part of a browser build.
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { NativeMachine, hex } from './machine.mjs';
import { PEImage } from './pe.mjs';

const root = fileURLToPath(new URL('../../', import.meta.url));
const target = JSON.parse(readFileSync(resolve(root, 'target.json'), 'utf8'));
const executable = /^[A-Za-z]:[\\/]/.test(target.executable)
  ? target.executable
  : resolve(root, target.executable);

const bytes = readFileSync(executable);
const sha256 = createHash('sha256').update(bytes).digest('hex');
if (sha256 !== target.sha256) throw new Error(`TH12 target hash mismatch: ${sha256}`);

const image = new PEImage(bytes);
const machine = await NativeMachine.create(bytes);

const summary = {
  executable,
  sha256,
  size: bytes.length,
  base: hex(image.base),
  entryPoint: hex(image.entryPoint ?? 0),
  headerSize: image.headerSize,
  sections: image.sections.map(section => ({
    name: section.name,
    rva: hex(section.rva),
    rawSize: section.rawSize,
    virtualSize: section.virtualSize,
    flags: `0x${(section.flags >>> 0).toString(16)}`,
  })),
  importCount: image.imports.length,
  importsByDll: {},
};

for (const entry of image.imports) {
  (summary.importsByDll[entry.dll] ??= []).push(entry.name);
}

machine.close();
console.log(JSON.stringify(summary, null, 2));
