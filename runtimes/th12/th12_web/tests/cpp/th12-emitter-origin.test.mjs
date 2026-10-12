import {touch,touchField} from './fixture-addresses.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {core,oracle,memory,report} from './helpers.mjs';
// TH12's 0x20d is the emitter-origin setter: th12.exe 0x417fab reads the emitter index from i(0), strides it
// by 0xc and writes origin.x from f(1), origin.y from f(2), then derives origin.z from an x87 comparison of
// origin.x against the double -990.0 at 0x4a3e70. The comparison is followed by `fnstsw ax` / `test ah,5` /
// `jp`, which reaches `fldz` exactly when one of C0 or C2 is set: x < -990 stores 0.0, and -990 itself as
// well as NaN store 1.0, because for NaN both flags are set and 0b101 has even parity. That boundary is the
// point of this test: a transcription that used `<=` or `!(x >= -990)` would differ at exactly -990 and at
// NaN, and neither value appears in ordinary stage data, so only a constructed example can tell them apart.
//
// The port keeps this as EnemyState::emitter_origin, whose offset is asked for rather than hardcoded, and the
// original keeps it at 0x158c. The dispatcher is called with the whole state on both sides and the three
// floats are compared, so the write offsets and the ordering against the argument reads are both covered.
const OFF=0x103c;
const ORIGINAL_ORIGIN=0x158c;
// Values that bracket the boundary. -990.0 and the two neighbours one float step away are the cases a wrong
// comparison operator gets wrong; NaN and the infinities cover the unordered path the `jp` encodes.
const SPECIAL=[-990.0,-1000.0,-900.0,-989.9999389648438,-990.0000610351563,0,-1,1e30,-1e30];
test('TH12 0x20d writes the emitter origin x, y and the derived z exactly as the original does',async()=>{
 const c=await core(),m=await oracle(),fixture=c.enemy_fixture_create(),enemy=c.enemy_fixture_data(fixture,0),p=enemy+OFF,world=c.enemy_fixture_data(fixture,2),context=c.allocate(0x1024),instruction=c.allocate(128),n=m.allocate(0x2a00),q=n+OFF,nb=m.allocate(0x2678),nc=m.allocate(0x1024),ni=m.allocate(128),nm=m.allocate(128),np=m.allocate(0x900);
 let seed=0x51ed,checks=0;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};const rand=()=>random()/4294967296;
 // The dispatcher reads [ebx+0x174c] as the script owner and then [that+4] as the context; the context's
 // +4 is the current instruction, which is where the opcode and the arguments come from. This is the same
 // chain the movement-command test builds, kept identical so a change in one place shows up in both.
 m.u32(touch(0x4a8d7c),nm);m.u32(nm+0x1c,nb);m.u32(touch(0x4a8eb4),np);m.u32(n,0x494074);m.u32(n+4,nc);m.u32(nc+4,ni);m.u32(q+0x174c,n);
 const originOffset=c.enemy_state_offset(1),offsetOffset=c.enemy_state_offset(2);
 assert.ok(originOffset>0&&originOffset+12<=0x2834,`emitter_origin offset ${originOffset} is inside the state`);
 assert.notEqual(originOffset,offsetOffset,'origin and offset are separate arrays');
 const contextBytes=Buffer.alloc(0x1024);contextBytes.writeUInt32LE(instruction,4);contextBytes.writeUInt32LE(enemy,0x1014);memory(c,context,contextBytes.length).set(contextBytes);
 try{
  for(let example=0;example<SPECIAL.length+120;++example){
   // The index has to stay in 0..7: the port guards it, while the original indexes without a bound check, so
   // an out-of-range example would compare a trap against a write outside the fixture. -990 and NaN decide
   // the comparison, not the index, so cycling the index over the same values loses nothing.
   const index=example%8;
   // NaN and the infinities are named rather than mixed into the random branch, so the unordered path is a
   // deliberate case and not something that might stop being generated if the sweep is ever reordered.
   const named=SPECIAL.length+1,positive=SPECIAL.length+2,negative=SPECIAL.length+3;
   const x=example<SPECIAL.length?SPECIAL[example]:(rand()-0.5)*4000;
   const y=example<SPECIAL.length?SPECIAL[SPECIAL.length-1-example]:(rand()-0.5)*4000;
   const xBits=example===named?0x7fc00000:example===positive?0x7f800000:example===negative?0xff800000:null;
   // Both sides are handed the same state before the command, and only the emitter region is compared, so a
   // difference in an unrelated field cannot be mistaken for a difference in this command's writes.
   const state=Buffer.alloc(0x1780);for(let i=0;i<0x1780;i+=4)state.writeUInt32LE(random(),i);
   state.writeFloatLE(x,0x14dc);state.writeFloatLE(y,0x14e0);
   const cs=Buffer.from(state),ns=Buffer.from(state);
   // The body strides the index by 0xc, so the slot that both sides must write is the indexed one. The sentinel
   // goes into that slot's z word, so a command that read the index but skipped the write cannot agree with the
   // other side by both having been handed the same input.
   cs.writeUInt32LE(0xdeadbeef,originOffset+12*index+8);ns.writeUInt32LE(0xdeadbeef,ORIGINAL_ORIGIN+12*index+8);
   cs.writeUInt32LE(0xdeadbeef,originOffset+12*index+4);ns.writeUInt32LE(0xdeadbeef,ORIGINAL_ORIGIN+12*index+4);
   memory(c,p,0x1780).set(cs);m.write(q,ns);m.u32(q+0x174c,n);
   const w=Buffer.alloc(24);w.writeUInt16LE(random()&65535);w.writeFloatLE(.5,8);w.writeFloatLE(0,16);memory(c,world,24).set(w);m.write(np+0x87c,w.subarray(12,24));
   const ins=Buffer.alloc(128);ins.writeUInt16LE(0x20d,4);ins.writeUInt16LE(128,6);ins[10]=255;ins[11]=8;
   ins.writeInt32LE(index,16);
   // A float argument is word 16 + index*4 for index >= 1. The x87 fetcher is indexed by the same number the
   // body pushes, so the two float words carry x and y in that order.
   if(xBits!==null)ins.writeUInt32LE(xBits,20);else ins.writeFloatLE(x,20);
   ins.writeFloatLE(y,24);
   ins.writeUInt16LE(0,8);
   memory(c,instruction,128).set(ins);m.write(ni,ins);
   m.resetThreadFPU();
   let expected;try{expected=m.call(0x4154d0,{ecx:q,edx:nc});}catch(error){error.message=`emulator fault at 0x20d case ${example} (index ${index}, x ${x}, y ${y}): ${error.message}`;throw error;}
   const actual=c.enemy_command(fixture,context);
   assert.equal(actual,expected,`return 0x20d/${example}`);
   const native=Buffer.from(m.bytes(q+ORIGINAL_ORIGIN+12*index,12)),port=Buffer.from(memory(c,p+originOffset+12*index,12));
   for(let k=0;k<12;++k)if(port[k]!==native[k]){
    const component=['x','y','z'][k>>2];
    assert.fail(`0x20d case ${example} index ${index} ${component}: cpp=${port.readFloatLE((k>>2)*4)} (${port.readUInt32LE((k>>2)*4).toString(16)}) native=${native.readFloatLE((k>>2)*4)} (${native.readUInt32LE((k>>2)*4).toString(16)}) x=${x} y=${y}`);
   }
   ++checks;
   // The neighbouring slots must be untouched: the body strides by 0xc and writes three floats, so a wrong
   // stride would corrupt the next emitter's origin, which comparing one slot alone would not notice.
   if(index<7){
    const neighbour=Buffer.from(memory(c,p+originOffset+12*(index+1),4)).readUInt32LE(0);
    assert.equal(neighbour,cs.readUInt32LE(originOffset+12*(index+1)),`0x20d/${example} wrote into origin[${index+1}].x`);
   }
  }
  // NaN is written as a word rather than through writeFloatLE, because a JS float64 NaN converts to the same
  // quiet NaN payload but the case is worth naming outright.
  report('emitter-origin',{passed:true,checks,special:SPECIAL.length,indexOffset:offsetOffset,scope:'TH12 0x20d (th12.exe 0x417fab) compared against the original dispatcher: emitter_origin[index].x from f(1), .y from f(2) and .z derived from an x87 comparison of x against the double -990.0, with -990 itself, its two float neighbours, NaN and the infinities in the sweep so the strictness of the comparison and the unordered path are both tested rather than assumed. The neighbouring origin slot is asserted unchanged.'});
 }finally{c.release(context);c.release(instruction);c.enemy_fixture_delete(fixture);m.close();}
});
