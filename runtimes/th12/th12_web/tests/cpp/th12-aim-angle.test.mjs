import {touch,touchField} from './fixture-addresses.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {core,oracle,memory,report} from './helpers.mjs';
// 0x208 at 0x4193ef writes the angle from a point to the player into the float variable named by the
// instruction's argument zero. The reference is resolved by 0x41a960 -> 0x4690b0, whose body reads:
//   mask = word [instruction+8] ; bit = 1 << index ; if (!(bit & mask)) return 0
//   if (argument slot == 0) return context + 8 + [context+0x100c] + index        (a stack local)
//   owner = [context+0x1014] ; vtable = [owner] ; id = 0x4931e0(slot) ; eax = vtable[0x10](owner, id)
// so with the reference bit set and a negative id the address comes from the owner's vtable slot 4. That is
// the same mask convention the port's EclContext::float_reference reads, and the same id space
// EnemyGlobals::float_reference implements directly (the note in enemy-commands.test.mjs records that the
// original virtual-calls the owner where the port looks the id up in a table).
//
// The measurements are the two things the transcription depends on:
//  * the angle, compared bit for bit between the original's store and the port's variable, and
//  * the mask convention, measured by whether the owner slot is called at all and with which id.
// A store that lands in the owner's target rather than in a variable would show up as a called slot with no
// matching value, and an implementation that read argument zero as a literal would show up as an uncalled slot.
const OFF=0x103c,PLAYER_X=0x97c,VARIABLE=-9981;
function instruction(mask,id,f1,f2){
 const ins=Buffer.alloc(128);
 ins.writeUInt16LE(0x208,4);ins.writeUInt16LE(128,6);ins[10]=255;ins[11]=8;
 ins.writeUInt16LE(mask,8);ins.writeFloatLE(id,16);ins.writeFloatLE(f1,20);ins.writeFloatLE(f2,24);
 return ins;
}
test('TH12 0x208 stores the angle to the player exactly where the original does',async()=>{
 const c=await core(),m=await oracle(),fixture=c.enemy_fixture_create();
 const q=m.allocate(0x2a00),n=m.allocate(0x2678),nc=m.allocate(0x1024),ni=m.allocate(128),nm=m.allocate(128),np=m.allocate(0x900);
 const player=m.allocate(0x1000),target=m.allocate(16),owner=m.allocate(64),vtable=m.allocate(64);
 const portContext=c.allocate(0x1024),portInstruction=c.allocate(128),portWorld=c.enemy_fixture_data(fixture,2);
 m.u32(touch(0x4a8d7c),nm);m.u32(touch(0x4a8eb4),np);m.u32(0x4b4514,player);
 m.u32(n,0x494074);m.u32(n+4,nc);m.u32(nc+4,ni);m.u32(q+0x174c,n);m.u32(nc+0x1014,owner);
 m.u32(owner,vtable);m.f32(target,0);
 const ownerCalls=[];let measuredOwnerArgument=null;
 m.u32(vtable+0x10,m.registerImport({dll:'aim-angle',name:'variable reference',argc:1,handler:()=>{ownerCalls.push(m.u32(m.reg('ESP')+4));return target;}}));
 const contextBytes=Buffer.alloc(0x1024);contextBytes.writeUInt32LE(portInstruction,4);memory(c,portContext,contextBytes.length).set(contextBytes);
 let seed=0x208,checks=0;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};
 const examples=[];
 // A zero vector is a real case: the original's atan2 receives (0, 0) whenever the point equals the player
 // position, and the port's aim_angle has a branch for it, so the comparison has to cover it rather than
 // step around it.
 for(let i=0;i<20;++i){
  const playerX=i===5?32.5:(random()%2000)/8-125,playerY=i===5?96.25:(random()%3000)/8-30;
  const pointX=i===5?playerX:(random()%4000)/16-125,pointY=i===5?playerY:(random()%4000)/16-30;
  examples.push([playerX,playerY,pointX,pointY]);
 }
 const zeroCount=examples.filter(([px,py,x,y])=>px===x&&py===y).length;
 assert.equal(zeroCount,1,'one example has the point exactly at the player position');
 for(const [playerX,playerY,pointX,pointY] of examples){
  const ins=instruction(1,VARIABLE,pointX,pointY);
  // The original side: the player position lives at [0x4b4514]+0x97c/+0x980 as a float pair, and the owner
  // slot returns the address the store uses.
  m.f32(player+PLAYER_X,playerX);m.f32(player+PLAYER_X+4,playerY);
  ownerCalls.length=0;m.f32(target,0);m.write(ni,ins);m.resetThreadFPU();
  const expected=m.call(0x4154d0,{ecx:q,edx:nc});
  assert.equal(expected,0,'the original returns 0');
  assert.equal(ownerCalls.length,1,'the original resolves argument zero exactly once');
  assert.equal(ownerCalls[0],VARIABLE>>>0,'the owner slot receives the variable id the slot names');
  measuredOwnerArgument=ownerCalls[0];
  const native=m.f32(target);
  // The port side: the same instruction bytes, the same id, and the fixture's environment holding the same
  // player position. The port reads the variable through EnemyGlobals::float_reference.
  memory(c,portWorld+12,12).set(Buffer.from(new Float32Array([playerX,playerY,0]).buffer));
  memory(c,portInstruction,128).set(ins);
  assert.equal(c.enemy_command(fixture,portContext),0,'the port returns 0');
  const actual=c.enemy_variable(fixture,VARIABLE,1);
  const rounded=Math.fround(actual);
  if(rounded!==native)assert.fail(`0x208 example (${playerX},${playerY})->(${pointX},${pointY}): original ${native} port ${actual}`);
  ++checks;
 }
 // A literal argument zero must not be written. The original does not guard this: measured, its resolver
 // returns 0 for a clear reference bit and 0x419629 is `fstp dword ptr [eax]`, so it faults on a null store.
 // The port's float_reference returns null and the case refuses to write, which is the difference between a
 // crash and a no-op and cannot change the meaning of any instruction the archives contain, since argument
 // zero is a reference in every one of them.
 {
  const ins=instruction(0,VARIABLE,10,20);
  m.f32(player+PLAYER_X,5);m.f32(player+PLAYER_X+4,6);
  ownerCalls.length=0;m.write(ni,ins);m.resetThreadFPU();
  let faulted=false;try{m.call(0x4154d0,{ecx:q,edx:nc});}catch(error){faulted=/WRITE_UNMAPPED|Invalid memory write/.test(error.message);}
  assert.equal(faulted,true,'the original faults when argument zero is not a reference');
  assert.equal(ownerCalls.length,0,'the original does not reach the owner slot for a literal argument');
  memory(c,portInstruction,128).set(ins);
  const before=c.enemy_variable(fixture,VARIABLE,1);
  assert.equal(c.enemy_command(fixture,portContext),-2,'the port reports an unresolved reference instead of writing through it');
  assert.equal(c.enemy_variable(fixture,VARIABLE,1),before,'the port writes nothing for a literal argument zero');
 }
 report('aim-angle',{passed:true,checks,examples:examples.length,zeroVectorExamples:zeroCount,ownerCallArguments:measuredOwnerArgument,scope:'TH12 0x208 (0x4193ef) against the original dispatcher. The original side resolves argument zero through the owner vtable slot 4 (0x4690f2..0x4690ff) with a registerImport stub that returns the store address, so the angle the original computes is read straight out of the address its own resolver produced; the port side reads the same variable id through enemy_variable. The mask convention is measured rather than assumed: the owner slot is called exactly once per example with the id from the instruction, and the literal case is measured to fault in the original and to no-op in the port.'});
 m.close();c.enemy_fixture_delete(fixture);
});
