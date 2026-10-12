import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {readEcl} from './ecl.mjs';
const path=new URL('../../runtimes/th06nc/artifacts/scripts/th06ST.dat/',import.meta.url);
const expected=[[38,745,231],[49,669,473],[61,1019,448],[119,2333,404],[75,1211,238],[87,1472,139],[145,3055,360]];
test('all seven original TH06nc ECL files consume every script boundary',()=>{
 for(let i=0;i<7;i++){
  const ecl=readEcl(readFileSync(new URL(`ecldata${i+1}.ecl`,path)));
  assert.deepEqual([ecl.subroutines.length,ecl.subroutines.reduce((n,s)=>n+s.instructions.length,0),
   ecl.timelines.filter(Boolean).reduce((n,s)=>n+s.instructions.length,0)],expected[i]);
  if(i===5)assert.ok(ecl.subroutines.some(s=>s.instructions.some(c=>c.opcode===201)));
 }
});
test('reject corrupted offsets, truncated files and instructions crossing a subroutine',()=>{
 const original=readFileSync(new URL('ecldata1.ecl',path));
 assert.throws(()=>readEcl(original.subarray(0,original.length-1)),/sentinel|truncated/);
 for(const mutate of [
  v=>v.setUint32(16,0,true),
  v=>v.setUint32(20,v.getUint32(16,true),true),
  v=>v.setUint16(v.getUint32(16,true)+6,65535,true),
  v=>v.setInt16(v.getUint32(20,true)-8,1,true),
 ]){
  const copy=Uint8Array.from(original);mutate(new DataView(copy.buffer));
  assert.throws(()=>readEcl(copy),/TH06nc ECL/);
 }
});
