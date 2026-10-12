import {touch,touchField} from './fixture-addresses.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {core,oracle,memory,report} from './helpers.mjs';
// SIZE is the compared window read back from the port through the core module, and it has to reach the
// port's indexed_values tail as well, because that field is now compared by translation. The original's
// state is larger still and its fields sit at its own offsets, so the buffer written into guest memory for
// the original needs its own bigger size; writing it re-asserts the fixture's invariants afterwards, because
// that write reaches offsets such as script_owner at 0x174c that the fixture set before it. Both windows are
// 0x1780, which stays inside the fixture's Enemy (0x2834 bytes from enemy through enemy+OFF).
const SIZE=0x1780,OFF=0x103c,NATIVE_SIZE=0x1780;
const timers=[0x154,0x174+48,0x1c0+48,...[0x20c,0x248,0x284,0x2c0,0x2fc,0x338].map(x=>x+32),0x1558,0x156c];
// Nondeterministic fields are zeroed before comparing, but the offsets belong to a layout: the port's timer
// bases only exist on the port's side. Applying them to the original's buffer zeroed unrelated fields - the
// port's 0x31c timer lands on 0x328, which for the original is start[1] of the 0x324 interpolator - and that
// is what round 89 chased all the way to the harness before it turned out to be this function.
function normalized(bytes,native){const b=Buffer.from(bytes);const bases=native?[0x324+0x20,0x360+0x20]:timers;for(const o of bases)b.writeUInt32LE(0,o+12);if(!native){b.writeUInt32LE(0,0x1614);b.writeUInt32LE(0,0x168);}return b;}
test('TH12 enemy movement commands match the original dispatcher including references and RNG order',async()=>{
 const c=await core(),m=await oracle(),fixture=c.enemy_fixture_create(),enemy=c.enemy_fixture_data(fixture,0),p=enemy+OFF,boss=c.enemy_fixture_data(fixture,1),world=c.enemy_fixture_data(fixture,2),context=c.allocate(0x1024),instruction=c.allocate(128),n=m.allocate(0x2a00),q=n+OFF,nb=m.allocate(0x2678),nc=m.allocate(0x1024),ni=m.allocate(128),nm=m.allocate(128),np=m.allocate(0x900);
 let checks=0,randomChecks=0,skippedReferenceExamples=0,seed=17391;const random=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed;};const rand=()=>random()/4294967296;
 m.u32(touch(0x4a8d7c),nm);m.u32(nm+0x1c,nb);m.u32(touch(0x4a8eb4),np);m.u32(n,0x494074);m.u32(n+4,nc);m.u32(nc+4,ni);m.u32(q+0x174c,n);
 // combine_movement (0x413700) reaches 0x468f4c, which reads [context+0x1014] as the owner, takes the
 // owner's first field as a vtable pointer and calls slot 3 through it. The Enemy is not such an object,
 // so the fixture supplies one. 0x402092 is a real `ret 4` tail of a function in the image, so landing
 // there executes only the return and pops the pushed float argument - the call becomes a no-op.
 const owner=m.allocate(0x100),vtable=m.allocate(0x40);m.u32(vtable+0x0c,0x402092);m.u32(owner,vtable);m.u32(nc+0x1014,owner);
 const contextBytes=Buffer.alloc(0x1024);contextBytes.writeUInt32LE(instruction,4);contextBytes.writeUInt32LE(enemy,0x1014);memory(c,context,contextBytes.length).set(contextBytes);
 const floatArgs=new Map([
  [0x118,[0,1]],[0x11a,[0,1]],[0x119,[2,3]],[0x11b,[2,3]],
  [0x11c,[0,1]],[0x11e,[0,1]],[0x11d,[2,3]],[0x11f,[2,3]],
  [0x120,[0,1,2,3]],[0x122,[0,1,2,3]],[0x121,[2,3,4]],[0x123,[2,3,4]],
  [0x124,[2]],[0x125,[2]],[0x126,[]],[0x127,[]],[0x128,[0,1,2]],[0x129,[0,1,2]],
  [0x12a,[0,1,2,3,4,5]],[0x12b,[0,1,2,3,4,5]],[0x12c,[0,1,2,3,4,5]],[0x12e,[0,1,2,3,4,5]],
  [0x12d,[2,3,4,5,6,7]],[0x12f,[2,3,4,5,6,7]],[0x130,[]],[0x131,[1,2,3,4,5,6]],[0x132,[1,2,3,4,5,6]],[0x133,[]],
  [0x192,[]],[0x193,[]],[0x20e,[]]
 ]);
 // Only opcodes measured as self-contained are compared here. tools/th12-opcode-probe.mjs runs each
 // command in a fresh oracle instance against this same bare fixture and reports which ones complete
 // a round trip; docs/th12/oracle-repointing.md §15 records the result. The rest need resources the
 // fixture cannot supply - the mSSSSS family stops in the name table - or trip machine-level faults,
 // so they are counted as skipped rather than compared against a run that never reached the command.
 // Only the bytes whose offsets agree between the two layouts are compared. The four Movements sit at
 // 0x0/0x34/0x68/0x9c in both, which the machine confirms: the 0x12c body addresses ebx+0x34, ebx+0x68 and
 // ebx+0x9c directly, and the fixture writes the same offsets on both sides. Past 0xd0 the port's layout is
 // 0xb8 bytes shorter than the original's and its interpolators live at different addresses, so comparing
 // those bytes would compare two different fields. The deferred byte count is reported so the narrowing
 // stays visible; re-widening needs the original's per-region offsets, not a guess.
 const COMPARABLE=0xd0;
 // Field pairs compared by translation, port offset against original offset. Only mappings that have
 // themselves been measured belong here: the clamp floats and the flags word qualify, established in rounds
 // 85 to 87. The interpolator blocks do not yet, for the reason recorded where they are copied below.
 const MAPPED=[[0x159c,0x16b8,4],[0x14dc,0x15f4,4],[0x14e0,0x15f8,4],[0x14e4,0x15fc,4],[0x14e8,0x1600,4]];
 // The animations table at 0xe0 is at the same offset in both layouts, which two independent readings agree on,
 // but an identity entry for it was added in round 99 and then removed in round 100: over 2688 compared examples
 // the region never changed on either side. 0x192 and 0x193 take its address with lea and hand it to a callee
 // that does not write it here, and 0x114, the one body that stores to it directly, faults in the probe on an
 // unreadable 0x130. An agreement between two buffers nobody wrote to is not evidence, so the entry is gone
 // rather than inflating mappedBytes with a comparison that can never see a difference. The invariant is
 // asserted below: when some opcode makes that region change, the assertion says so and the entry can return.
 // The 0x3c interpolator blocks are only comparable for opcodes whose bodies actually write them. The
 // 0x131/0x133/0x149 family does - 0x131 writes the original's 0x324, 0x133 its 0x360 - and comparing them
 // there is what tests the +0x360 = relative_angle assumption. Opcode 0x119 is the counter-example: its
 // original body writes the indexed float array at [ebx+eax*4+0x1e0], not an interpolator, so the mapping
 // does not apply and the comparison would compare unrelated fields.
 const MAPPED_INTERP=[[0x20c,0x324,0x3c],[0x248,0x360,0x3c]];
 const INTERPOLATOR_OPS=new Set([0x119,0x131,0x133,0x149]);
 // 0x119's array. The port keeps it as a named member, so the entry is built at run time from the export
 // rather than hardcoding an offset the struct can move. 0x1e0 is the original's base and 96 bytes is indices
 // 0..23, the furthest the case bodies were measured to reach in docs/th12/state-offsets.json; the original's
 // next separate field 0x26c and its interpolator at 0x324 both fall outside that length, so nothing else is
 // dragged into the comparison.
 const INDEXED_OFFSET=c.enemy_state_offset(0);
 const MAPPED_ALL=MAPPED.concat([[INDEXED_OFFSET,0x1e0,0x60]]);
 const SELF_CONTAINED=new Set([0x119,0x11a,0x11c,0x120,0x124,0x128,0x12a,0x12c,0x12e,0x131,0x133,0x192,0x193,0x20e]);
 const skippedOpcodes=[];
 // Round 99 added the identity mapping for 0xe0 but could not show the region changes at all, so these count
 // it. A comparison that never observes a difference is not evidence: if the region is identical to what each
 // side was handed, the entry only proves neither implementation touched it.
 let e0ChangedPort=0,e0ChangedNative=0,e0ChangedEither=0;
 try{
 for(const[op,args]of floatArgs){
  if(!SELF_CONTAINED.has(op)){skippedOpcodes.push(op);continue;}
  for(let example=0;example<252;++example){
  const state=Buffer.alloc(SIZE);for(const o of[0,0x34,0x68,0x9c]){for(let j=0;j<12;++j)state.writeFloatLE((rand()-.5)*(j<6?500:j===8?70:6),o+j*4);state.writeUInt32LE(example%4,o+48);}
  for(let o=0x124;o<0x154;o+=4)state.writeFloatLE((rand()-.5)*10,o);
  for(const[o,components]of[[0x174,3],[0x1c0,3],[0x20c,2],[0x248,2],[0x284,2],[0x2c0,2],[0x2fc,2],[0x338,2]]){for(let j=0;j<components*4;++j)state.writeFloatLE((rand()-.5)*20,o+j*4);state.writeInt32LE(3,o+components*16);state.writeInt32LE(4,o+components*16+4);state.writeFloatLE(4.25,o+components*16+8);state.writeUInt32LE(example%2,o+components*16+16);state.writeInt32LE(9,o+components*16+20);state.writeInt32LE(example%18,o+components*16+24);}
  const flags=(example%2?0x8000:0)|(example%3?0x2000:0);state.writeUInt32LE(flags,0x1580);state.writeFloatLE(0,0x14dc);state.writeFloatLE(220,0x14e0);state.writeFloatLE(380,0x14e4);state.writeFloatLE(440,0x14e8);
  // 0x119 writes one element of the 0x1e0 array and leaves the rest alone, unlike the interpolator bodies that
  // overwrite their whole block. The other elements therefore have to be equal on both sides before the call.
  // The pattern lives in its own buffer rather than being seeded through `state`, because this port's array
  // offset 0x16b8 is where the original keeps its flags word, so a seed written at that offset in `state`
  // would reach the original as flags and clobber them.
  const indexedSeed=Buffer.alloc(0x60);for(let j=0;j<24;++j)indexedSeed.writeInt32LE((rand()*1000)|0,j*4);
  const cs=Buffer.from(state),ns=Buffer.alloc(NATIVE_SIZE);state.copy(ns);for(const o of timers){cs.writeUInt32LE(world+8,o+12);ns.writeUInt32LE(0x4a7948,o+12);}cs.writeUInt32LE(enemy,0x1614);ns.writeUInt32LE(n,0x1614);memory(c,p,SIZE).set(cs);m.write(q,ns);
  // The write above covers the original's whole state region, so it reaches offsets the fixture set before
  // it - script_owner at 0x174c above all, which the dispatcher reads as [ebx+0x174c] at 0x415512 and then
  // dereferences at 0x415518. Leaving it zero there is what produced round 86's fault at pc 0x415518
  // reading address 0x4: not the enlargement as such, but the enlargement clobbering the fixture's own
  // invariant. Re-asserting it makes the larger write safe.
  m.u32(q+0x174c,n);
  // Per-side offsets, now that the original's own layout is addressable. combine_movement's clamp is gated
  // on bit 16 of the flags word, which the port keeps at 0x159c and the original at 0x16b8, and it reads
  // four floats at 0x15f4/0x15f8/0x15fc/0x1600 there against the port's clamp_center/clamp_size at
  // 0x14dc/0x14e0/0x14e4/0x14e8 here. Setting the bit makes the clamp path reachable on both sides; without
  // it both skip the branch and the condition round 85 changed is never taken. The fixture's centres 0/220
  // and sizes 380/440 put many positions outside the box, so the clamp fires and its effect on
  // current.position, which is inside the compared region, is compared.
  const FLAG_CLAMP=0x10000;
  // Input translation, driven by the same lists the comparison uses, so a new mapping entry cannot be
  // compared without also being given the same content on both sides at their own addresses. That is the rule
  // round 94 arrived at the hard way: the 0x131 family passed without it only because those bodies overwrite
  // their whole block, while 0x119 writes one element and inherits the rest from its input. Two details are
  // per-entry: the timer's elapsed is zeroed on the original side to match what normalized() does for the
  // port, and the indexed array comes from its own buffer rather than from `state`, because this port's array
  // offset 0x16b8 is where the original keeps its flags word.
  for(const[po,no,n]of MAPPED_ALL.concat(MAPPED_INTERP)){
    ns.set(no===0x1e0?indexedSeed:cs.subarray(po,po+n),no);
    if(n===0x3c)ns.fill(0,no+0x2c,no+0x30);
  }
  // Setting the clamp bit makes the clamp path reachable on both sides; without it both skip the branch and
  // the condition round 85 changed is never taken. It is set after the translation above, which carries the
  // flags word, so the copy cannot clear it again.
  cs.writeUInt32LE(cs.readUInt32LE(0x159c)|FLAG_CLAMP,0x159c);
  ns.writeUInt32LE(ns.readUInt32LE(0x16b8)|FLAG_CLAMP,0x16b8);
  // The port's Interpolator<float,2> has the original's layout field for field: start[2], end[2],
  // initial_tangent[2], final_tangent[2], Timer, duration at +0x34, mode at +0x38, 0x3c bytes in all, which
  // is also the stride between the fixture's blocks and between the original's 0x324 and 0x360. Only the
  // base differs, so the same bytes can be compared once each side has them: the 0x131/0x133/0x149 family
  // writes the port's absolute_angle 0x20c and relative_angle 0x248 against the original's 0x324 and 0x360,
  // and comparing that block is what turns the +0x360 = relative_angle assumption into a tested claim.
  // The Timer's elapsed is zeroed at +0x2c on the original side by the translation loop above, to match what
  // normalized() does for the port.
  // The indexed array is translated by the same loop, from its seed buffer, for the same reason: both sides
  // must start from the same pattern at their own address, otherwise the untouched elements differ for a
  // reason that has nothing to do with either implementation. 0x60 bytes is 24 entries, the measured reach.
  cs.set(indexedSeed,INDEXED_OFFSET);ns.set(indexedSeed,0x1e0);
  memory(c,p,SIZE).set(cs);m.write(q,ns);m.u32(q+0x174c,n);
  const w=Buffer.alloc(24);w.writeUInt16LE(random()&65535);w.writeFloatLE(example%2?.375:1,8);w.writeFloatLE((rand()-.5)*300,12);w.writeFloatLE(rand()*440,16);memory(c,world,24).set(w);m.write(touch(0x4c2f00),w.subarray(0,8));m.write(touch(0x4a7948),w.subarray(8,12));m.write(np+0x87c,w.subarray(12,24));
  const bossPosition=Buffer.alloc(12);for(let j=0;j<3;++j)bossPosition.writeFloatLE((rand()-.5)*200,j*4);memory(c,boss+OFF+0x34,12).set(bossPosition);m.write(nb+OFF+0x34,bossPosition);
  const ins=Buffer.alloc(128);ins.writeUInt16LE(op,4);ins.writeUInt16LE(128,6);ins[10]=255;ins[11]=8;ins.writeInt32LE(example%43-2,16);ins.writeInt32LE(example%18,20);let references=0;
  for(const index of args){let value=(rand()-.5)*8;if((example+index)%7===0)value=-999999;else if((example+index)%11===0)value=-1000000;
   if(example%4===3){value=[-9999,-9998,-9987,-9981,-9971,-9969][(example+index)%6];references|=1<<index;}
   ins.writeFloatLE(value,16+index*4);
  }
  // References to the same RNG variable reveal non-source-order argument reads.
  if(example%9===0){for(const index of args){ins.writeFloatLE(-9998,16+index*4);references|=1<<index;}}
  ins.writeUInt16LE(references,8);memory(c,instruction,128).set(ins);m.write(ni,ins);
  // Arguments whose reference bit is set carry a TH12 global variable ID, and the original resolves those
  // with a virtual call: at 0x468f4c it loads the owner from context+0x1014, takes the owner's first field
  // as a vtable and calls slot 3 with the converted argument. The fixture's owner can only hold the `ret 4`
  // stub it needs for combine_movement, which returns without producing an accessor value, while the port's
  // EnemyGlobals::floating implements those IDs directly. The two sides therefore cannot agree on this path
  // and the comparison is deferred rather than faked; the count is reported so the gap stays visible.
  if(references){++skippedReferenceExamples;continue;}
  m.resetThreadFPU();let expected;try{expected=m.call(0x4154d0,{ecx:q,edx:nc});}catch(error){error.message=`emulator fault at opcode 0x${op.toString(16)} case ${example}: ${error.message}`;throw error;}assert.equal(c.enemy_command(fixture,context),expected,`return ${op.toString(16)}/${example}`);
  const a=normalized(memory(c,p,SIZE),false),b=normalized(m.bytes(q,NATIVE_SIZE),true);
  // Did the 0xe0 table actually change? cs and ns still hold exactly what each side was handed at the write
  // above, since everything after it only reads them, so they are the pre-command snapshot. normalized() zeroes
  // timer words, and no timer lies inside 0xe0..0x120, so the region is comparable as it stands.
  {const p0=!a.subarray(0xe0,0x120).equals(cs.subarray(0xe0,0x120)),n0=!b.subarray(0xe0,0x120).equals(ns.subarray(0xe0,0x120));
   if(p0)++e0ChangedPort;if(n0)++e0ChangedNative;if(p0||n0)++e0ChangedEither;}
  // Field-mapped comparison. Beyond the movement region the two layouts no longer share offsets, so a range
  // cannot simply be widened; each entry below pairs a port offset with the original offset that the
  // machine code was measured to use for the same field. The clamp floats and the flags word were
  // established in rounds 85 to 87; the two 0x3c interpolator blocks are equivalent because the port's
  // Interpolator<float,2> reproduces the original's layout.
  // Only mappings that have themselves been measured are compared. The clamp floats and the flags word
  // qualify: rounds 85 to 87 established the flags word by its mask set and the clamp floats by the
  // original reading 0x15f4/0x15f8/0x15fc/0x1600 while a falsification showed the branch executing. The
  // two 0x3c interpolator blocks are deliberately NOT here yet. Their copy above is in place and the
  // port's Interpolator<float,2> is field-for-field the original's layout, but comparing them immediately
  // reported original+0x324 as zero where the port holds -9.600165367126465 on a no-op opcode, and that
  // has to be explained as either a mapping error or a real difference before it is called a defect.
  // The pairs to compare are declared at module scope, next to COMPARABLE.
  for(const[po,no,n]of(INTERPOLATOR_OPS.has(op)?MAPPED_ALL.concat(MAPPED_INTERP):MAPPED_ALL)){let k=0;while(k<n&&a[po+k]===b[no+k])++k;if(k<n)assert.fail(`command 0x${op.toString(16)} case ${example} mapped field port+0x${po.toString(16)} vs original+0x${no.toString(16)} at +0x${k.toString(16)} PREBUFF port=${cs.readFloatLE(po+k)} native=${ns.readFloatLE(no+k)}: cpp=${a.readFloatLE(po+k)} (${a.readUInt32LE(po+k).toString(16)}) native=${b.readFloatLE(no+k)} (${b.readUInt32LE(no+k).toString(16)}) | current x cpp=${a.readFloatLE(0x34)} native=${b.readFloatLE(0x34)} | abs x cpp=${a.readFloatLE(0x68)} native=${b.readFloatLE(0x68)} | ins +0x10=${ins.readInt32LE(16)} +0x14=${ins.readInt32LE(20)} refs=0x${references.toString(16)}`);}
  const same=(()=>{for(let i=0;i<COMPARABLE;++i)if(a[i]!==b[i])return false;return true;})();if(!same){let o=0;while(o<COMPARABLE&&a[o]===b[o])++o;o&=~3;assert.fail(`command 0x${op.toString(16)} case ${example} offset 0x${o.toString(16)} cpp=${a.readFloatLE(o)} (${a.readUInt32LE(o).toString(16)}) native=${b.readFloatLE(o)} (${b.readUInt32LE(o).toString(16)}) | current x cpp=${a.readFloatLE(0x34)} native=${b.readFloatLE(0x34)} | abs x cpp=${a.readFloatLE(0x68)} native=${b.readFloatLE(0x68)} | rel x cpp=${a.readFloatLE(0x9c)} native=${b.readFloatLE(0x9c)} | velocity x cpp=${a.readFloatLE(0x40)} native=${b.readFloatLE(0x40)} | ins +0x10=${ins.readInt32LE(16)} +0x14=${ins.readInt32LE(20)} refs=0x${references.toString(16)}`);}++checks;
  assert.deepEqual(Buffer.from(memory(c,world,8)),Buffer.from(m.bytes(0x4c2f00,8)),`rng ${op.toString(16)}/${example}`);++randomChecks;
 }
 }
 // Recorded invariant, not a statistic. Round 99 mapped 0xe0 by identity and round 100 measured that no example
 // changes it, so the entry is gone. This asserts the measurement that removed it: if some opcode later makes
 // the region change, this fails and says the identity entry can be brought back with evidence behind it.
 assert.equal(e0ChangedEither,0,`the 0xe0 region changed on ${e0ChangedEither} of ${checks} examples, so the identity entry removed in round 100 is justified again and should return`);
 report('enemy-commands',{passed:true,checks,randomChecks,skippedReferenceExamples,comparedBytes:COMPARABLE,deferredBytes:SIZE-COMPARABLE,mappedFields:MAPPED_ALL.length,mappedBytes:MAPPED_ALL.reduce((s,e)=>s+e[2],0),opcodes:[...SELF_CONTAINED],skippedOpcodes,e0ChangedPort,e0ChangedNative,e0ChangedEither,scope:'movement commands verified against TH12\'s dispatcher: a byte comparison over the first 0xd0 bytes, where both layouts place the same four Movements, plus a field-mapped comparison of the flags word, the four clamp floats and the two 0x3c interpolator blocks that the 0x131/0x133/0x149 family writes - each mapped entry pairs a port offset with the original offset the machine code was measured to use for that field, because past the movement region the two layouts no longer share offsets and a range cannot simply be widened. RNG state, sentinel inputs and the preserved center-command fallthrough are checked too, for the opcodes measured as self-contained in §15. Fields whose mapping is not yet measured, and examples whose arguments carry reference bits (the original resolves those through an owner virtual call the fixture cannot implement), are deferred and counted, not claimed. The 0xe0 identity entry added in round 99 is gone: it was measured to be inert, since no example changed that region on either side over 2688 comparisons, and the lane now asserts that measurement so the entry can return when some opcode does change it.'});
 }finally{c.release(context);c.release(instruction);c.enemy_fixture_delete(fixture);m.close();}
});
