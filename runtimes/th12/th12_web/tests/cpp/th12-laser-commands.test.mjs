import {touch,touchField} from './fixture-addresses.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {core,oracle,memory,report} from './helpers.mjs';
// TH12's 0x25c, 0x25d and 0x262 all begin by finding a laser by id. The helper every one of them calls is
// 0x412960, read instruction for instruction: `if (!id) return 0; for (o = [mgr+0x18]; o; o = [o+8]) if
// (o[0x80] == id) return o; return 0`. The port's LaserManager::find is the same function, including the
// id-zero short circuit, so both sides here build the same shape of list and the commands are compared on
// the bytes of the object they touch rather than on a return value alone.
//
// The two commands that write a vector store the fetched float words unchanged, so this compares raw bytes:
// the original writes +0x50..+0x58 for 0x25c and +0x460..+0x468 for 0x25d, and the port writes its own
// position and velocity, whose offsets are asked for rather than typed in. A byte comparison catches a
// conversion through double, which a comparison with a tolerance would not.
//
// The original side fabricates its laser list - two objects linked through +0x8 with ids at +0x80 - and the
// port side fabricates one through lm_inject, which links an object into LaserManager the same way the
// original's spawn function does at 0x41bb40. Nothing here depends on a loaded animation, so a difference in
// the comparison is a difference in the command and not in the fixture.
const OFF=0x103c;
const ID=0x80,NEXT=0x8,POSITION=0x50,VELOCITY=0x460,VTABLE=0x0;
const REWARD_EVENT=5,EFFECT_EVENT=4;
// Finite values with exact bit patterns, plus both zeros, so a store through double shows up. NaN is left out
// deliberately: the original copies the word while the port assigns a float, and quieting a signalling NaN is
// a difference that would say nothing about the offsets this test is about.
const SPECIALS=[0,-0,1.5,-2.25,0.1,1e30,-1e30,3.4028234663852886e38];
function instruction(op,id,a,b){
 const ins=Buffer.alloc(128);
 ins.writeUInt16LE(op,4);ins.writeUInt16LE(128,6);ins[10]=255;ins[11]=8;
 ins.writeUInt32LE(id>>>0,16);
 ins.writeFloatLE(a,20);ins.writeFloatLE(b,24);
 ins.writeUInt16LE(0,8);
 return ins;
}
test('TH12 0x25c and 0x25d write the found laser exactly as the original does',async()=>{
 const c=await core(),m=await oracle(),fixture=c.enemy_fixture_create(),enemy=c.enemy_fixture_data(fixture,0),p=enemy+OFF,world=c.enemy_fixture_data(fixture,2),context=c.allocate(0x1024),instructionPointer=c.allocate(128),n=m.allocate(0x2a00),q=n+OFF,nb=m.allocate(0x2678),nc=m.allocate(0x1024),ni=m.allocate(128),nm=m.allocate(128),np=m.allocate(0x900);
 let seed=0x6f11,checks=0;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
 m.u32(touch(0x4a8d7c),nm);m.u32(nm+0x1c,nb);m.u32(touch(0x4a8eb4),np);m.u32(n,0x494074);m.u32(n+4,nc);m.u32(nc+4,ni);m.u32(q+0x174c,n);
 const manager=m.allocate(0x800),laserA=m.allocate(0x1100),laserB=m.allocate(0x1100);
 m.u32(0x4b44f4,manager);m.u32(manager+0x18,laserA);m.u32(laserA+NEXT,laserB);m.u32(laserB+NEXT,0);
 const positionOffset=c.laser_offset(5),velocityOffset=c.laser_offset(6),typeOffset=c.laser_offset(4);
 assert.equal(c.laser_size(),0x440,'the port\'s LaserState is still the 0x440-byte TH11-derived layout');
 assert.notEqual(positionOffset,velocityOffset,'position and velocity are separate fields');
 const contextBytes=Buffer.alloc(0x1024);contextBytes.writeUInt32LE(instructionPointer,4);contextBytes.writeUInt32LE(enemy,0x1014);memory(c,context,contextBytes.length).set(contextBytes);
 const lm=c.lm_create();
 try{
  const w=Buffer.alloc(24);w.writeUInt16LE(random()&65535);w.writeFloatLE(.5,8);memory(c,world,24).set(w);m.write(np+0x87c,w.subarray(12,24));
  for(const [op,nativeOffset,portOffset] of [[0x25c,POSITION,positionOffset],[0x25d,VELOCITY,velocityOffset]]){
   // The port's list starts empty and one laser is injected per example, plus a second one when the matching id
   // must be found through the next link rather than at the head.
   for(let example=0;example<24;++example){
    const infinite=(example&4)!==0,matchesFirst=(example&2)===0;
    const idOther=0x1000+example,target=0x2000+example,idA=matchesFirst?target:idOther,idB=matchesFirst?idOther:target;
    c.lm_clear(lm);
    const firstLaser=c.lm_inject(lm,idA,infinite?1:0),secondLaser=c.lm_inject(lm,idB,infinite?1:0);
    assert.ok(firstLaser&&secondLaser,`the port list holds two lasers (example ${example})`);
    const sentinel=0xdeadbeef;
    for(const laser of [firstLaser,secondLaser]){const block=Buffer.alloc(12);for(let k=0;k<12;k+=4)block.writeUInt32LE(sentinel,k);memory(c,laser+portOffset,12).set(block);}
    const fill=Buffer.alloc(0x1100);for(let i=0;i<0x1100;i+=4)fill.writeUInt32LE(0xcdcdcdcd,i);
    // The link goes into the object's own buffer: writing the objects after setting the chain would overwrite
    // +0x8 with the fill pattern, and find would then walk to the sentinel instead of to the second laser.
    const build=(id,next)=>{const b=Buffer.from(fill);b.writeUInt32LE(next,NEXT);b.writeUInt32LE(id,ID);for(let k=0;k<12;k+=4)b.writeUInt32LE(sentinel,nativeOffset+k);return b;};
    m.write(laserA,build(idA,laserB));m.write(laserB,build(idB,0));
    const a=SPECIALS[example%SPECIALS.length],b=example<SPECIALS.length?-SPECIALS[example%SPECIALS.length]:(random()|0)/64;
    const ins=instruction(op,target,a,b);
    memory(c,instructionPointer,128).set(ins);m.write(ni,ins);
    m.resetThreadFPU();
    let expected;try{expected=m.call(0x4154d0,{ecx:q,edx:nc});}catch(error){error.message=`emulator fault at 0x${op.toString(16)} example ${example}: ${error.message}`;throw error;}
    const actual=c.lm_enemy_command(lm,fixture,context);
    assert.equal(actual,expected,`return 0x${op.toString(16)}/${example}`);
    assert.equal(expected,0,`0x${op.toString(16)} returns 0 through the shared epilogue (example ${example})`);
    // The native side must have written {f(1), f(2), 0}, so the bytes the port is compared against are the
    // original's rather than this test's expectation.
    const want=Buffer.alloc(12);want.writeFloatLE(a,0);want.writeFloatLE(b,4);want.writeFloatLE(0,8);
    const foundNative=matchesFirst?laserA:laserB,nativeBytes=Buffer.from(m.bytes(foundNative+nativeOffset,12));
    for(let k=0;k<12;++k)assert.equal(nativeBytes[k],want[k],`the original must write {f(1),f(2),0} at +0x${nativeOffset.toString(16)} (example ${example})`);
    const foundPort=matchesFirst?firstLaser:secondLaser,portBytes=Buffer.from(memory(c,foundPort+portOffset,12));
    for(let k=0;k<12;++k)if(portBytes[k]!==nativeBytes[k])assert.fail(`0x${op.toString(16)}/${example} byte ${k}: cpp=${portBytes[k].toString(16)} native=${nativeBytes[k].toString(16)}`);
    // The object that was not found keeps its sentinel on both sides, which is what makes the comparison
    // evidence about the id walk and the write together rather than about a command that wrote every laser.
    const untouchedPort=matchesFirst?secondLaser:firstLaser,untouchedNative=matchesFirst?laserB:laserA;
    assert.equal(Buffer.from(memory(c,untouchedPort+portOffset,4)).readUInt32LE(0),sentinel,`the port wrote the laser that does not match the id (example ${example})`);
    assert.equal(Buffer.from(m.bytes(untouchedNative+nativeOffset,4)).readUInt32LE(0),sentinel,`the original wrote the laser that does not match the id (example ${example})`);
    if(op===0x25d)assert.equal(memory(c,foundPort+typeOffset,1)[0],infinite?1:0,`type of the laser 0x25d wrote (example ${example})`);
    ++checks;
   }
  }
  // An id that no laser carries is a no-op on both sides, which covers the find-miss path and the return value.
  for(const op of [0x25c,0x25d,0x262]){
   c.lm_clear(lm);assert.equal(c.lm_count(lm),0,'the manager is empty');
   m.u32(manager+0x18,0);
   const ins=instruction(op,0x7f7f,1,2);memory(c,instructionPointer,128).set(ins);m.write(ni,ins);m.resetThreadFPU();
   const expectedMissing=m.call(0x4154d0,{ecx:q,edx:nc}),actualMissing=c.lm_enemy_command(lm,fixture,context);
   assert.equal(expectedMissing,0,`the original's 0x${op.toString(16)} with no matching laser returns 0`);
   assert.equal(actualMissing,expectedMissing,`0x${op.toString(16)} with no matching laser`);
   ++checks;
  }
  report('laser-vector-commands',{passed:true,checks,positionOffset,velocityOffset,scope:'TH12 0x25c (0x418f0c) and 0x25d (0x418f66, through 0x412900) compared against the original dispatcher on raw bytes. Both sides build a two-object list through [0x4b44f4]+0x18 and +0x8, the matching id alternates between the head and the second object, and the laser type alternates so 0x25d\'s LaserInfiniteParameters sync is exercised. The non-matching object keeps its sentinel on both sides, and an id no laser carries returns 0 on both sides, so the comparison is evidence about the id walk, the write and the miss path together.'});
 }finally{c.lm_delete(lm);c.release(context);c.release(instructionPointer);c.enemy_fixture_delete(fixture);m.close();}
});
test('TH12 0x262 cancels every laser with the id and pays no reward, as the original does',async()=>{
 const c=await core(),m=await oracle(),fixture=c.enemy_fixture_create(),enemy=c.enemy_fixture_data(fixture,0),context=c.allocate(0x1024),instructionPointer=c.allocate(128),n=m.allocate(0x2a00),q=n+OFF,nb=m.allocate(0x2678),nc=m.allocate(0x1024),ni=m.allocate(128),nm=m.allocate(128),np=m.allocate(0x900);
 m.u32(touch(0x4a8d7c),nm);m.u32(nm+0x1c,nb);m.u32(touch(0x4a8eb4),np);m.u32(n,0x494074);m.u32(n+4,nc);m.u32(nc+4,ni);m.u32(q+0x174c,n);
 // The virtual cancel is reached through the object's own vtable slot +0x14 with two zero arguments, so the
 // native side installs a host stub that records the `this` pointer and both arguments. The count distinguishes
 // "every matching object was cancelled" from "the first one was", and the arguments are what the transcription
 // must reproduce: passing reward = 1 would pay graze rewards the original does not.
 const slot=m.allocate(16),called=[],pushed=[];
 m.replace(slot,'laser-cancel',()=>{called.push(m.reg('ECX'));pushed.push([m.u32(m.reg('ESP')+4),m.u32(m.reg('ESP')+8)]);return 0;},2);
 const vtable=m.allocate(0x20);m.u32(vtable+0x14,slot);
 const manager=m.allocate(0x800),laserA=m.allocate(0x1100),laserB=m.allocate(0x1100),laserC=m.allocate(0x1100);
 m.u32(0x4b44f4,manager);m.u32(manager+0x18,laserA);
 const target=0x3344,other=0x5566;
 // The chain is written into each object's buffer rather than with u32 afterwards, so the fill cannot clobber the
 // next pointer and send find to the sentinel.
 for(const [laser,id,next] of [[laserA,target,laserB],[laserB,target,laserC],[laserC,other,0]]){
  const bytes=Buffer.alloc(0x1100);for(let i=0;i<0x1100;i+=4)bytes.writeUInt32LE(0xcdcdcdcd,i);
  bytes.writeUInt32LE(vtable,VTABLE);bytes.writeUInt32LE(next,NEXT);bytes.writeUInt32LE(id,ID);
  m.write(laser,bytes);
 }
 const ins=instruction(0x262,target,0,0);memory(c,instructionPointer,128).set(ins);m.write(ni,ins);
 m.resetThreadFPU();
 const expected=m.call(0x4154d0,{ecx:q,edx:nc});
 assert.equal(expected,0,'0x262 returns 0');
 assert.equal(called.length,2,`the original cancels both objects with the id, not ${called.length}`);
 assert.deepEqual(called.slice().sort((x,y)=>x-y),[laserA,laserB].sort((x,y)=>x-y),'the stub is called with each matching object');
 assert.equal(pushed.length,2,'both cancelled objects are recorded');
 assert.deepEqual(pushed,[[0,0],[0,0]],'every cancelled object is cancelled with both arguments zero');
 // Neither object is the head of the list here, so the loop's re-find is what reaches the second one: a body that
 // cancelled only the first find result would leave one id behind.
 for(const laser of [laserA,laserB])assert.equal(m.u32(laser+ID),0,`the original clears the id at +0x80 (0x${laser.toString(16)})`);
 assert.equal(m.u32(laserC+ID),other,'the original leaves the object with a different id alone');
 const contextBytes=Buffer.alloc(0x1024);contextBytes.writeUInt32LE(instructionPointer,4);contextBytes.writeUInt32LE(enemy,0x1014);memory(c,context,contextBytes.length).set(contextBytes);
 const lm=c.lm_create(),lengthOffset=c.laser_offset(8),angleOffset=c.laser_offset(7);
 try{
  c.laser_fixture_count(lm,2);
  // The port's lasers are given a length past the 16 the cancel body needs and a position inside the reward box,
  // so the reward arm of that body is reachable: a transcription that reused cancel_id, which passes reward =
  // true, would push a reward event here and this assertion is what catches it.
  const l0=c.lm_inject(lm,target,0),l1=c.lm_inject(lm,target,0),l2=c.lm_inject(lm,other,0);
  for(const laser of [l0,l1]){memory(c,laser+lengthOffset,4).set(Buffer.from([0,0,0xc8,0x42]));memory(c,laser+angleOffset,4).fill(0);const pos=Buffer.alloc(12);pos.writeFloatLE(0);pos.writeFloatLE(100,4);memory(c,laser+c.laser_offset(5),12).set(pos);}
  assert.equal(c.lm_find(lm,target),l0,'find returns the first matching laser before the command');
  const actual=c.lm_enemy_command(lm,fixture,context);
  assert.equal(actual,expected,'the port returns what the original returns');
  assert.equal(c.lm_find(lm,target),0,'no laser with the id is left');
  assert.equal(c.lm_find(lm,other),l2,'the laser with a different id is left alone');
  const count=c.laser_fixture_count(lm,0),events=c.laser_fixture_data(lm,3),view=new DataView(c.memory.buffer);
  const kinds=[];for(let i=0;i<count;++i)kinds.push(view.getInt32(events+i*20,true));
  assert.ok(kinds.includes(EFFECT_EVENT),`the cancel body ran (events ${JSON.stringify(kinds)})`);
  assert.equal(kinds.includes(REWARD_EVENT),false,`0x262 must not pay the reward cancel_id would (events ${JSON.stringify(kinds)})`);
  report('laser-cancel-id',{passed:true,nativeCalls:called.length,eventKinds:kinds,target,other,scope:'TH12 0x262 (0x418ebd) compared against the original dispatcher. The native side records each vtable slot +0x14 call through a host stub and asserts both pushed arguments are zero, so "both objects with the id" is a count and the (0,0) is a measurement rather than a reading. The port side injects three lasers with two sharing the id, gives them a length past the cancel body\'s 16 and a position inside the reward box, and asserts the cancel-effect event is present while the reward event is absent - which is the assertion that would fail if the transcription had reused cancel_id and its reward = true.'});
 }finally{c.lm_delete(lm);c.release(context);c.release(instructionPointer);c.enemy_fixture_delete(fixture);m.close();}
});
