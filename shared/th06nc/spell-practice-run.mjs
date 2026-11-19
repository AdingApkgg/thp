import {spellPracticeStartingPower} from './spell-practice-power.mjs';
const U=n=>BigInt.asUintN(64,BigInt(n??0));

// 3b018..3b0d4. 4ff0f0/1 are live stocks; the continue-default snapshots at
// c21de0/1 were copied earlier and remain unchanged here.
export function initializeSpellPracticeRun(environment){
 Object.assign(environment,{spellEnemyStarted:false,spellRunState:0,spellRunClock:0,spellRunBossLife:1,spellRunSurvival:false,spellFinished:false,playerPower:spellPracticeStartingPower(environment.spellPracticeIndex),lives:0,bombs:0});
 return environment;
}

// Game-owner spell branch 3a42c..3a626, after its ordinary pause/owner gates.
// Result painting and user actions belong to the result owner.
export function advanceSpellPracticeRun(environment,{records,boss=null,bossState,fade=null}={}){
 const e=environment;if(!e.spellPractice)return null;
 const score=U(e.score),playback=Boolean(e.replayPlayback),id=e.spellPracticeIndex&255;
 if(!playback){
  const profile=(e.character&255)*2+(e.shot&255),index=(e.difficulty|0)*4+profile,record=records?.get(id);
  if(!record||id>=134||index<0||index>=20)throw Error('TH06nc: spell run record missing or invalid');
  const v=new DataView(record.bytes.buffer,record.bytes.byteOffset,record.bytes.byteLength),offset=0x40+index*8;
  if(v.getBigUint64(offset,true)<score)v.setBigUint64(offset,score,true);
 }
 const state=e.spellRunState|0;
 if(state===0){if(bossState?.active)e.spellRunState=1;}
 else if(state===1){
  if(boss){e.spellRunBossLife=boss.v.getInt32(0x234,true);e.spellRunSurvival=Boolean(boss.v.getUint8(0xbe)&16);}
  if(!bossState?.active&&!(e.spellCounter|0)){e.spellRunClock=120;e.spellRunState=2;}
 }else if(state===2){
  if(boss)e.spellRunBossLife=boss.v.getInt32(0x234,true);
  e.spellRunClock=((e.spellRunClock|0)-1)|0;
  if(e.spellRunClock<=0){
   if(playback){fade?.requestOut(0,30);e.spellRunState=4;}
   else{
    const captured=(e.spellRunBossLife|0)<=0||Boolean(e.spellRunSurvival);e.spellResultVisible=true;e.displayScore=score;e.spellRunState=3;
    return {kind:'spellPracticeResult',captured,score};
   }
  }
 }else if(state===4&&fade?.mode===2)e.gameState=8;
 return null;
}
