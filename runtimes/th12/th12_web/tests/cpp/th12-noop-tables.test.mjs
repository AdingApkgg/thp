import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {core,root,report} from './helpers.mjs';
// The port answers an opcode from a per-title table, because whether a number does anything is read from each
// title's own executable: the dispatch guard rejects everything above its range, and inside the range the group
// table hands some numbers to a handler that only advances the script pointer. TH12's table is the control - it was
// first derived by disassembling the dispatcher and recording which opcodes reach its epilogue at 0x41962b - so the
// test asserts that the two derivations agree bit for bit, then checks the other five columns against the recorded
// document the generator wrote.
const document=JSON.parse(readFileSync(resolve(root,'../../../docs/porting/noop-opcodes.json'),'utf8'));
const TITLES=[['th12',12],['th13',13],['th14',14],['th16',16],['th17',17],['th18',18]];
test('per-title no-op tables match their executables and TH12 agrees with the dispatcher-derived table',async()=>{
 const c=await core();
 let checks=0,noops=0,permuted=0;
 for(const[name,number]of TITLES){
  const row=document.titles[name],first=Number(row.first),last=Number(row.last);
  const expected=new Set(row.noops.map(op=>Number(op)));
  assert.equal(expected.size,row.noopCount,`${name} document lists ${row.noopCount} no-ops but holds ${expected.size}`);
  // Every permitted opcode, and a band above the range: past `last` the predicate has to be true because the guard's
  // rejection is itself a no-op, which is a claim about the executable and not a convenience of the table.
  for(let op=first;op<=last;++op){
   const want=expected.has(op)?1:0;
   assert.equal(c.noop_probe(number,op),want,`${name} opcode 0x${op.toString(16)}`);
   ++checks;
   if(want)++noops;
  }
  for(const op of [last+1,last+2,last+0x100,0xffff]){
   assert.equal(c.noop_probe(number,op),1,`${name} opcode 0x${op.toString(16)} is past the guard and must be a no-op`);
   ++checks;
  }
  // Below the range the value is not a command at all: it belongs to the interpreter's own operations, which are
  // dispatched before the command layer, so the predicate has to say it is not a jumped-over command.
  for(let op=0;op<first;++op){assert.equal(c.noop_probe(number,op),0,`${name} opcode 0x${op.toString(16)} is below the range`);++checks;}
  permuted+=last-first+1;
 }
 // The two TH12 derivations, over a window wide enough to include both ends and the out-of-range bands.
 for(let op=0;op<=0x400;++op){
  const legacy=c.noop_legacy_probe(op),perTitle=c.noop_probe(12,op),runtime=c.noop_runtime_probe(op);
  assert.equal(perTitle,legacy,`TH12 opcode 0x${op.toString(16)}: per-title table says ${perTitle}, the dispatcher-derived table says ${legacy}`);
  assert.equal(runtime,perTitle,`TH12 opcode 0x${op.toString(16)}: this build selected another title's table (runtime ${runtime})`);
  ++checks;
 }
 // The build has to be running the title its workspace names, otherwise every handler gate below is answering with
 // another title's table and nothing else in the suite would notice.
 // The discriminator is taken from the two columns instead of being written down, so it cannot go stale the
 // way a literal does: it must be a number TH12 skips, TH13 dispatches, and this build must answer with
 // TH12's table. TH13's family now runs to 0x3eb, so plenty of numbers qualify; 0x20d does not - it
 // resolves to 0x41e3fd there, and that body opens with a call (e8 6e c8 ff ff), so TH13 acts on it.
 const th12Noops=document.titles.th12.noops.map(Number),th13First=Number(document.titles.th13.first),
       th13Last=Number(document.titles.th13.last),th13Noops=new Set(document.titles.th13.noops.map(Number));
 const split=th12Noops.find(op=>op>=th13First&&op<=th13Last&&!th13Noops.has(op));
 assert.ok(split!==undefined,'the two columns must differ inside the range they share');
 assert.equal(c.noop_probe(12,split),1,`0x${split.toString(16)} does nothing in TH12`);
 assert.equal(c.noop_probe(13,split),0,`0x${split.toString(16)} acts in TH13`);
 assert.equal(c.noop_runtime_probe(split),c.noop_probe(12,split),'this build must select TH12');
 report('noop-tables',{passed:true,checks,permuted,noops,titles:TITLES.map(([name])=>name),scope:'Each title\'s no-op predicate compared against the table derived from its own executable, over every permitted opcode plus bands below and above the range, and TH12\'s two independent derivations compared bit for bit: the per-title table generated from handler bodies and the table the dispatcher disassembly recorded. The build is asserted to select TH12.'});
});
