import {initializeRunCardAttackScores} from './gameplay-card-attack.mjs';
import {loadCardAttackScores,loadClearedScores,loadPracticeScores,initializeTitleCardAttackScores,loadMusicScores} from './score-stat-load.mjs';
import {createSpellRecord} from './spell-record.mjs';
// Exact global span 4f1e8c..4ff164. PSCR's accepted loading span overlaps
// the first CATK slot. Keep views in one buffer so title load order preserves
// this observable effect, rather than giving each record type separate storage.
export class ScoreStats {
 constructor(initial=new Uint8Array(0xd2d8)){
  if(!(initial instanceof Uint8Array)||initial.length!==0xd2d8)throw Error('TH06nc score stats: invalid global span');
  this.bytes=initial.slice();this.optionalRecords=this.bytes.subarray(0,96*24);this.practiceLoadSpan=this.bytes.subarray(0,101*24);this.cardAttack=this.bytes.subarray(0x93c,0x93c+134*384);this.cleared=this.bytes.subarray(0xd268,0xd268+96);this.music=this.bytes.subarray(0xd2c8,0xd2d8);
  this.spellRecords=new Map(Array.from({length:134},(_,id)=>[id,createSpellRecord(this.cardAttack.subarray(id*384,(id+1)*384),{copy:false})]));
 }
 // New-run initializer: random defaults, CATK load, then PSCR load. The
 // latter's wider accepted span can alias the first CATK, as in the native.
 loadRun(records,rng){initializeRunCardAttackScores(this.cardAttack,rng);loadCardAttackScores(records,this.cardAttack);loadPracticeScores(records,this.practiceLoadSpan);}
 loadBoot(records){this.music.set(loadMusicScores(records));}
 loadTitle(records){this.cleared.set(loadClearedScores(records));loadPracticeScores(records,this.practiceLoadSpan);initializeTitleCardAttackScores(records,this.cardAttack);}
 // Native Result 7430c..74457 skips disk stats for name entry (9) and
 // practice result (17); state 17 updates the existing unsigned best score.
 loadResult(records,{state,character=0,shot=0,stage=1,difficulty=0,score=0n}){
  if(state!==9&&state!==17){loadCardAttackScores(records,this.cardAttack);this.cleared.set(loadClearedScores(records));loadPracticeScores(records,this.practiceLoadSpan);}
  if(state===17){const p=(((character*2+shot)*6+stage-1)*4+difficulty)*24+12,v=new DataView(this.bytes.buffer),candidate=BigInt.asUintN(64,BigInt(score));if(v.getBigUint64(p,true)<candidate)v.setBigUint64(p,candidate,true);}
 }
}
