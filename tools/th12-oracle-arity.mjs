// Decide whether one of the inherited th11 test addresses can be repointed at a th12 function.
//
// The oracle tests call original functions with a calling convention baked into the test:
//   m.call(0x412e30, {ecx: ...})                 <- one register argument
// A th12 counterpart may not share that shape - FUN_004154d0 turned out to read EDX as well - and
// swapping the address alone would then produce calls with the wrong arguments. This tool reports
// the facts needed to decide, straight from the decompiler output:
//
//   * the calling convention in the decompiler's own signature
//   * how many parameters it takes and in which registers
//   * whether each declared parameter is actually read anywhere in the body
//
// Usage:
//   node tools/th12-oracle-arity.mjs 0x4154d0 [0x412010 ...]
//
// Exit code is 0 always; this reports evidence, it does not authorise an edit.
import { readFileSync, readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ws = resolve(fileURLToPath(new URL('..', import.meta.url)));
const decomp = resolve(ws, 'reference/th12-decomp/decomp_out');

const normalize = value => {
  const n = Number(value);
  if (!Number.isFinite(n)) throw new Error(`Not an address: ${value}`);
  return Math.trunc(n);
};
const pad = va => '0x' + va.toString(16).padStart(8, '0');

// __fastcall delivers the first two arguments in ECX and EDX, the rest on the stack.
const convention = (calling, count) => {
  const regs = [];
  if (calling === 'fastcall') {
    if (count >= 1) regs.push('ECX');
    if (count >= 2) regs.push('EDX');
    for (let i = 3; i <= count; ++i) regs.push(`STACK+${(i - 3) * 4}`);
  } else if (calling === 'thiscall') {
    if (count >= 1) regs.push('ECX=this');
    for (let i = 2; i <= count; ++i) regs.push(`STACK+${(i - 2) * 4}`);
  } else {
    for (let i = 1; i <= count; ++i) regs.push(`STACK+${(i - 1) * 4}`);
  }
  return regs;
};

const addresses = process.argv.slice(2).map(normalize);
if (addresses.length === 0) {
  console.error('usage: node tools/th12-oracle-arity.mjs <va> [va ...]');
  process.exit(2);
}

const files = readdirSync(decomp);
const report = [];

for (const va of addresses) {
  const suffix = `_${va.toString(16).padStart(8, '0')}.c`;
  const file = files.find(name => name.endsWith(suffix));
  if (!file) {
    report.push({ va: pad(va), found: false });
    continue;
  }
  const text = readFileSync(resolve(decomp, file), 'utf8');
  const lines = text.split('\n');
  const header = lines[0] ?? '';
  // /* undefined __fastcall FUN_004154d0(void * param_1, int * param_2) @ 004154d0  16758 bytes */
  const parsed = /^\/\*\s*(.*?)\s+(@\s+[0-9a-fA-F]+\s+\d+ bytes)\s*\*\/$/.exec(header.trim());
  const signature = parsed ? parsed[1] : header.trim();
  const callingMatch = /\b(__cdecl|__fastcall|__stdcall|__thiscall)\b/.exec(signature);
  const calling = callingMatch ? callingMatch[1].replace(/^__/, '') : 'cdecl';
  const argsMatch = /\(([^)]*)\)/.exec(signature);
  const rawArgs = argsMatch && argsMatch[1].trim() !== '' && argsMatch[1].trim() !== 'void'
    ? argsMatch[1].split(',').map(a => a.trim())
    : [];
  const params = rawArgs.map((decl, index) => {
    const paramName = new RegExp(`\\bparam_${index + 1}\\b`);
    const uses = lines.slice(1).filter(line => paramName.test(line)).length;
    return { decl, name: `param_${index + 1}`, uses, read: uses > 0 };
  });
  const registers = convention(calling, params.length);
  report.push({
    va: pad(va),
    found: true,
    file,
    calling,
    signature,
    bytes: parsed ? parsed[2] : null,
    parameters: params.map((p, i) => ({
      decl: p.decl,
      register: registers[i] ?? '?',
      readInBody: p.read,
      occurrences: p.uses,
    })),
  });
}

for (const entry of report) {
  if (!entry.found) {
    console.log(`${entry.va}  NO DECOMPILED FILE - cannot decide, do not swap`);
    continue;
  }
  console.log(`${entry.va}  ${entry.file}`);
  console.log(`  signature : ${entry.signature}`);
  console.log(`  calling   : ${entry.calling}  (${entry.parameters.length} parameter(s))`);
  if (entry.parameters.length === 0) {
    console.log('  parameters: none');
  } else {
    for (const p of entry.parameters) {
      const flag = p.readInBody ? 'read' : '*** NEVER READ IN BODY ***';
      console.log(`  parameter : ${p.register.padEnd(8)} ${p.decl}  -> ${flag} (${p.occurrences} lines)`);
    }
  }
  const unread = entry.parameters.filter(p => !p.readInBody && p.name !== 'param_1');
  if (unread.length > 0) {
    console.log(`  WARNING   : ${unread.map(p => p.name).join(', ')} declared but never read - the`);
    console.log('              decompiler may have invented it; confirm against the disassembly');
    console.log('              prologue before relying on the register layout.');
  }
  console.log('');
}
