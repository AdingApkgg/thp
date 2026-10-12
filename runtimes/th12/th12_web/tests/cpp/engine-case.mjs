// One engine acceptance case, in a process of its own.
//
// Section 67 of docs/porting/porting-plan.md: after one wasm-side trap, every later call in the
// same process fails the same way, and not even resetThreadFPU heals it. So a case BOX can hold many
// measurements, a process cannot. This file is the child of engine-acceptance.mjs and prints one
// JSON line; it never imports the fixture, so a run says what the engine does with the shipped
// bytes and nothing else.
//
//   node engine-case.mjs '{"entry":"0x402551","mode":"bare","implant":"c3"}'
//
// mode: raw (a fresh NativeMachine.create), bring (plus resetThreadFPU), bare (hooks deleted),
//       oracle (helpers.mjs's bring-up, i.e. the fixture's machine).
// implant: hex bytes written at the entry after loading, before the start.
// frame: esp (default m.stack), pushReturn (write m.returnAddress at esp), exit (an `int 3` sentinel)
//        - the default frame is the harness's own: esp = m.stack, return address on top.
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {NativeMachine} from '../../scripts/native/machine.mjs';
import {root,target,sha} from './helpers.mjs';

const hex=n=>'0x'+(Number(n)>>>0).toString(16);
const spec=JSON.parse(process.argv[2]);
const entry=Number(spec.entry);
const bytes=readFileSync(resolve(root,target.executable));
if(sha(bytes)!==target.sha256)throw Error('th12 target hash mismatch');

let m;
if(spec.mode==='oracle')m=await (await import('./helpers.mjs')).oracle();
else{
  m=await NativeMachine.create(bytes);
  if(spec.mode==='bring')m.resetThreadFPU();
  if(spec.mode==='bare'){for(const hook of m.hooks)m.cpu.hook_del(hook);m.hooks.length=0;}
}
let verdict,detail='',trace;
if(spec.trace){
  const seen=[];
  m.cpu.hook_add(m.uc.HOOK_CODE,(cpu,address)=>{if(seen.length<Number(spec.trace))seen.push(hex(address));},
    null,entry,entry+0x100);
  trace=seen;
}
if(spec.implant)m.write(entry,Buffer.from(spec.implant,'hex'));
const object=m.allocate(Number(spec.objectSize??0x40000));
const front=m.allocate(0x1000);
m.reg('ESP',Number(spec.esp??m.stack));
if(spec.frame!=='noreturn')m.u32(m.reg('ESP'),m.returnAddress);
m.reg('ESI',spec.esi==='front'?front:object);
if(spec.edi!==undefined)m.reg('EDI',Number(spec.edi));
try{
  m.cpu.emu_start(entry,m.returnAddress,0,Number(spec.limit??200000));
  verdict=m.reg('EIP')===m.returnAddress?'ok':'stopped';
  detail='eip='+hex(m.reg('EIP'));
}catch(error){
  const text=String(error.message??error).split('\n')[0];
  verdict=text.includes('memory access out of bounds')?'trap':'guest';
  detail=text.slice(0,72);
}
console.log(JSON.stringify({spec,verdict,detail,...(trace?{trace}:{})}));
