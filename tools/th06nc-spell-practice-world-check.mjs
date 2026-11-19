import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
import {StageWorld} from '../shared/th06nc/stage-world.mjs';
import {AnmBank} from '../shared/th06nc/anm-bank.mjs';
import {readAnm} from '../shared/th06nc/anm.mjs';
import {readEcl} from '../shared/th06nc/ecl.mjs';
import {stageAssetPlan} from '../shared/th06nc/stage-layout.mjs';
import {commonProjectileAssetPlan,stageEffectAssetPlan} from '../shared/th06nc/common-layout.mjs';
import {readSpellPracticeTable} from '../shared/th06nc/spell-practice-table.mjs';
import {NativeRng} from '../shared/th06nc/rng.mjs';
import {PlayerState} from '../shared/th06nc/player-state.mjs';
import {playerAssetPlan} from '../shared/th06nc/player-init.mjs';
import {readStd} from '../shared/th06nc/std.mjs';
import {stdAssetPlan} from '../shared/th06nc/std-state.mjs';
import {spellPracticeStartingPower} from '../shared/th06nc/spell-practice-power.mjs';
import {initialGameplayRank} from '../shared/th06nc/gameplay-start-settings.mjs';
import {initializeSpellPracticeRun,advanceSpellPracticeRun} from '../shared/th06nc/spell-practice-run.mjs';
import {createSpellRecord} from '../shared/th06nc/spell-record.mjs';
const sources=['enemy-world','stage-world','std','std-state','std-update','spell-practice-background','spell-practice-power','spell-practice-run','spell-record','gameplay-start-settings','spell-practice-spawn','enemy-pool','ecl-dispatch','ecl-tick','enemy-phase','player-state','player-init','spell-state','bullet-pool','laser-pool','effect-pool'].map(s=>'shared/th06nc/'+s+'.mjs'),sha=b=>createHash('sha256').update(b).digest('hex'),snapshot=()=>Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))])),sourceSha256=snapshot();
const table=readSpellPracticeTable(readFileSync('runtimes/th06nc/artifacts/scripts/th06IN.dat/spellpractice.msgpack')),stages=new Map(),evidence=[];
for(let stage=1;stage<=7;stage++){
 const refs=[...stageAssetPlan(stage).enemyAnimations,...commonProjectileAssetPlan(),stageEffectAssetPlan(stage),stdAssetPlan(stage),playerAssetPlan(0),...([6,7].includes(stage)?[{archive:'th06ST.dat',file:'eff0'+stage+'.anm',slot:11,base:0x2d3}]:[])];
 stages.set(stage,{std:readStd(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/stage'+stage+'.std')),refs,resources:refs.map(ref=>readAnm(readFileSync('runtimes/th06nc/artifacts/scripts/'+ref.archive+'/'+ref.file))),program:readEcl(readFileSync('runtimes/th06nc/artifacts/scripts/th06ST.dat/ecldata'+stage+'.ecl'))});
}
const timeoutMode=process.argv.includes('--timeout');
for(const row of timeoutMode?table.filter(r=>[0,70,129,130].includes(r.id)):table){
 const stage=row.stageIndex+1,{refs,resources,program,std}=stages.get(stage),bank=new AnmBank();refs.forEach((ref,i)=>bank.load(resources[i],ref.base,{slot:ref.slot}));
 const environment={spellPractice:true,spellPracticeIndex:row.id,spellEnemyStarted:false,difficulty:row.difficulty,character:0,shot:0,rank:initialGameplayRank(row.difficulty),stageIndex:stage,playerPower:spellPracticeStartingPower(row.id),rng:new NativeRng(0xbeef),playerPosition:[192,400,0],aimTarget:[192,400,0],score:0n,atan2:Math.atan2,messageField36b0:-1},intros=[];
 initializeSpellPracticeRun(environment);
 const player=new PlayerState({anmBank:bank,environment}),world=new StageWorld(program,{anmBank:bank,environment,player,stdProgram:std,sin:Math.sin,cos:Math.cos,atan2:Math.atan2,spellPracticeTable:table,publishSpellIntro:r=>intros.push(r),bodyCollision:()=>0,bulletCollision:()=>0,laserCollision:()=>0,damageQuery:()=>({damage:0,critical:false})});
 world.enemies.spellState.records=new Map(Array.from({length:134},(_,id)=>[id,createSpellRecord()]));
 let runEvent=null,frames=0;try{for(;frames<(timeoutMode?16000:240);){world.tick();frames++;runEvent=advanceSpellPracticeRun(environment,{records:world.enemies.spellState.records,boss:world.enemies.bossSlots[0],bossState:world.enemies.bossState});if(timeoutMode&&runEvent)break;}if(timeoutMode){assert.equal(environment.spellFinished,true,'real script timeout did not finish');assert.equal(runEvent?.kind,'spellPracticeResult');assert.equal(runEvent.captured,world.enemies.spellState.records.get(row.id).practiceCaptures[row.difficulty*4]>0);}}catch(error){throw Error('Spell '+row.id+' stage '+stage+' sub '+row.subroutine+': '+error.message,{cause:error});}
 assert.equal(environment.spellEnemyStarted,true);assert.equal(world.enemies.timeline.cursor,null,'ordinary stage timeline ran');assert.equal(world.enemies.timeline.messageClock%1800,0);
 assert.equal(intros.length,1,'one spell introduction for '+row.id);assert.equal(environment.spellId,row.id);assert.equal(intros[0].key,row.name);assert.equal(world.enemies.spellState.records.get(row.id).practiceAttempts[row.difficulty*4],1);
 const record=world.enemies.spellState.records.get(row.id),bestScore=new DataView(record.bytes.buffer,record.bytes.byteOffset,record.bytes.byteLength).getBigUint64(0x40+row.difficulty*32,true);assert.equal(bestScore,BigInt(environment.score));
 const actors=world.enemies.pool.entries.filter(Boolean);assert.ok(actors.length>0);evidence.push({id:row.id,stage,subroutine:row.subroutine,frames,bestScore:String(bestScore),result:runEvent?{...runEvent,score:String(runEvent.score)}:null,backgroundPreparation:world.spellBackgroundPreparation,backgroundSha256:sha(world.background.owner),finished:Boolean(environment.spellFinished),spellCounter:environment.spellCounter,intro:intros[0].key,actors:actors.length,bullets:world.bullets.activeCount,laserSha256:sha(world.lasers.storage),enemySha256:sha(world.enemies.pool.storage),bulletSha256:sha(world.bullets.storage),effectSha256:sha(world.effects.storage),rng:{seed:environment.rng.seed,count:environment.rng.count}});
}
assert.deepEqual(snapshot(),sourceSha256);const report={scope:'All 131 original catalog entries launched through StageWorld/EnemyWorld with actual ECL/STD and enemy/projectile/effect/background ANMs for 240 ticks each. Real ECL, enemy, bullet, laser, effect, player/item update and CATK attempt paths; ReimuA with input 0, collision/damage services disabled, no message/HUD/audio/GPU or native per-frame comparison. Verifies stage timeline suppression, one spell intro with matching ID/key and one practice attempt; no natural player clear/save/replay acceptance claim.',cases:evidence.length,frames:evidence.reduce((n,e)=>n+e.frames,0),evidence,sourceSha256,passed:true,completeGame:false,nativeEquivalent:false};if(timeoutMode)report.scope='Original spell IDs 0/70/129/130 through real ECL/STD timeout/completion with unmodified HP and timers, input 0 and collision/damage services disabled; real player/enemy/projectile/effect/item updates and one CATK practice attempt. Includes the 120-frame result delay and result publication request; no message/HUD/audio/GPU, native per-frame comparison, natural player clear or result UI/save/replay acceptance claim.';writeFileSync(timeoutMode?'docs/porting/th06nc-spell-practice-timeout-world-verified.json':'docs/porting/th06nc-spell-practice-world-verified.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:evidence.length,frames:report.frames}));
