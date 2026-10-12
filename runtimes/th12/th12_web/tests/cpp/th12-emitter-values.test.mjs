import {touch,touchField} from './fixture-addresses.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {core,oracle,memory,report} from './helpers.mjs';
// TH12's 0x259 stores five integers into the emitter named by i(0): th12.exe 0x4186cd calls the integer fetcher six
// times, strides the first result by 0x214 and writes the other five at +0x670 through +0x680 relative to the enemy.
// The dispatcher's emitter base is +0x48c, so the write offsets are emitter+0x1e4 through +0x1f4 - a block that was a
// single reserved run in the port until these five offsets were measured. The probe that measured them is in this
// round's notes: with i(0) at 0, 1, 3 and 7 the writes land at +0x670, +0x884, +0xcac and +0x14fc, which is
// 0x670 + index*0x214 exactly, and each block receives i(1)..i(5) in order.
//
// The original writes them with dword moves and then returns through the shared epilogue at 0x41962b, so the return
// value is 0 and the neighbouring emitter is untouched. Both are asserted here, because a wrong stride would corrupt
// the next emitter and comparing one block alone would not notice.
const OFF=0x103c;
const ORIGINAL_VALUES=0x670,ORIGINAL_STRIDE=0x214;
test('TH12 0x259 stores five integers into the indexed emitter exactly as the original does',async()=>{
 const c=await core(),m=await oracle(),fixture=c.enemy_fixture_create(),enemy=c.enemy_fixture_data(fixture,0),p=enemy+OFF,world=c.enemy_fixture_data(fixture,2),context=c.allocate(0x1024),instruction=c.allocate(128),n=m.allocate(0x2a00),q=n+OFF,nb=m.allocate(0x2678),nc=m.allocate(0x1024),ni=m.allocate(128),nm=m.allocate(128),np=m.allocate(0x900);
 let seed=0x2c9b,checks=0;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};const rand=()=>random()/4294967296;
 m.u32(touch(0x4a8d7c),nm);m.u32(nm+0x1c,nb);m.u32(touch(0x4a8eb4),np);m.u32(n,0x494074);m.u32(n+4,nc);m.u32(nc+4,ni);m.u32(q+0x174c,n);
 const stride=c.emitter_stride(),baseOffset=c.emitter_offset(0),valuesOffset=c.emitter_offset(1);
 assert.equal(stride,ORIGINAL_STRIDE,'the port\'s emitter stride must be the original\'s 0x214');
 assert.ok(baseOffset+stride*8<=0x1780,'the whole emitter array fits inside the window both sides are given');
 const contextBytes=Buffer.alloc(0x1024);contextBytes.writeUInt32LE(instruction,4);contextBytes.writeUInt32LE(enemy,0x1014);memory(c,context,contextBytes.length).set(contextBytes);
 try{
  for(let example=0;example<160;++example){
   // All eight emitter indices, because the stride is what is being tested: an off-by-one in the multiply would pass
   // for index 0 and fail for every other one.
   const index=example%8;
   // Arguments that exercise the sign and the full width: the original fetches them as integers and stores the words
   // unchanged, so a port that went through a float conversion would differ on the large and negative values.
   const chosen=[];
   for(let k=1;k<=5;++k){
    const pattern=[0,1,-1,0x7fffffff,-0x80000000,random()|0,(example*7+k)|0,0x12345678];
    chosen.push(pattern[(example+k)%pattern.length]);
   }
   const state=Buffer.alloc(0x1780);
   for(let i=0;i<0x1780;i+=4)state.writeUInt32LE(0xcdcdcdcd,i);
   // The emitter block the command writes is filled with a sentinel rather than the pattern, so a command that
   // skipped the write cannot agree with the other side merely because both were handed the same input.
   for(let k=0;k<5;++k){state.writeUInt32LE(0xdeadbeef,valuesOffset+index*stride+k*4);}
   const cs=Buffer.from(state),ns=Buffer.from(state);
   memory(c,p,0x1780).set(cs);m.write(q,ns);m.u32(q+0x174c,n);
   const w=Buffer.alloc(24);w.writeUInt16LE(random()&65535);w.writeFloatLE(.5,8);memory(c,world,24).set(w);m.write(np+0x87c,w.subarray(12,24));
   const ins=Buffer.alloc(128);ins.writeUInt16LE(0x259,4);ins.writeUInt16LE(128,6);ins[10]=255;ins[11]=8;
   ins.writeInt32LE(index,16);
   for(let k=1;k<=5;++k)ins.writeInt32LE(chosen[k-1],16+k*4);
   ins.writeUInt16LE(0,8);
   memory(c,instruction,128).set(ins);m.write(ni,ins);
   m.resetThreadFPU();
   let expected;try{expected=m.call(0x4154d0,{ecx:q,edx:nc});}catch(error){error.message=`emulator fault at 0x259 case ${example} (index ${index}): ${error.message}`;throw error;}
   const actual=c.enemy_command(fixture,context);
   assert.equal(actual,expected,`return 0x259/${example}`);
   assert.equal(expected,0,`0x259 must return 0 through the shared epilogue (case ${example})`);
   const native=Buffer.from(m.bytes(q+ORIGINAL_VALUES+index*ORIGINAL_STRIDE,20));
   const port=Buffer.from(memory(c,p+valuesOffset+index*stride,20));
   for(let k=0;k<5;++k){
    const want=chosen[k]>>>0;
    assert.equal(native.readUInt32LE(k*4),want,`the original must store i(${k+1}) (case ${example})`);
    assert.equal(port.readUInt32LE(k*4),want,`0x259/${example} values_1e4[${k}]: cpp=${port.readUInt32LE(k*4).toString(16)} native=${native.readUInt32LE(k*4).toString(16)}`);
   }
   ++checks;
   // For every index but the first, the block at the *unindexed* offset has to stay untouched on both sides. Without
   // this the test would still pass if both sides wrote a constant place, which is exactly the failure a missing
   // multiply produces, so the assertion is what makes the offsets above evidence of the index arithmetic.
   if(index>0){
    assert.equal(Buffer.from(m.bytes(q+ORIGINAL_VALUES,20)).equals(ns.subarray(ORIGINAL_VALUES,ORIGINAL_VALUES+20)),true,`0x259/${example} the original wrote the unindexed block too`);
    assert.equal(Buffer.from(memory(c,p+valuesOffset,20)).equals(cs.subarray(valuesOffset,valuesOffset+20)),true,`0x259/${example} the port wrote the unindexed block too`);
   }
   // The neighbour, reached by the same multiply: 0x214 bytes on, the first word must still be exactly what the state
   // was handed there. Comparing against the input rather than a literal is what makes this a stride check.
   if(index<7){
    const neighbour=Buffer.from(memory(c,p+valuesOffset+(index+1)*stride,4)).readUInt32LE(0);
    assert.equal(neighbour,cs.readUInt32LE(valuesOffset+(index+1)*stride),`0x259/${example} wrote into emitter ${index+1}`);
   }
  }
  report('emitter-values',{passed:true,checks,stride,baseOffset,valuesOffset,scope:'TH12 0x259 (th12.exe 0x4186cd) compared against the original dispatcher: i(0) is the emitter index, strided by the original\'s 0x214, and i(1) through i(5) are stored at emitter+0x1e4 through +0x1f4 with a dword move. Every one of the eight indices is exercised, so a wrong multiply fails, and the neighbouring emitter is asserted untouched so a wrong stride cannot pass by comparing a single block. The values cover zero, both signs, both 32-bit extremes and random words, since the original stores the fetched words unchanged.'});
 }finally{c.release(context);c.release(instruction);c.enemy_fixture_delete(fixture);m.close();}
});
