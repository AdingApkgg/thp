// Where the ANM load stops, and with what fault - one measured call per process.
//
// The fixture's `load()` is one `m.call` into the game, so a load that fails leaves a payload
// (the harness's MEM_UNMAPPED hook, imported in scripts/native/machine.mjs) plus the registers and
// stack at that instant. Print the pc, the registers and the first stack words, then look the pc
// up in the portable reference (tools/th-code-region.py) and the decompiled candidate.
//
// One call per process (section 67: a wasm-side trap poisons every later call in the same
// process), which is what this file exists for.
//
//   node anm-load-fault.mjs [name.anm]
import {oracle} from './helpers.mjs';
import {animationOracle} from './anm-oracle.mjs';
const hex=n=>'0x'+(Number(n)>>>0).toString(16);
const m=await oracle(),o=animationOracle(m);
const name=process.argv[2]??'text.anm';
try{
  const loaded=o.load(name);
  console.log(JSON.stringify({name,verdict:'ok',original:hex(loaded.original),heap:hex(loaded.heap)}));
}catch(error){
  const text=String(error.message??error);
  console.log(JSON.stringify({name,verdict:'failed',message:text.split('\n')[0],
    fault:text.split('\n').slice(1).join(' ').slice(0,240),
    registers:['EIP','ESP','EBP','EAX','EBX','ECX','EDX','ESI','EDI'].map(r=>r+'='+hex(m.reg(r))).join(' '),
    stack:m.readWords(m.reg('ESP'),10).map(hex)}));
}
