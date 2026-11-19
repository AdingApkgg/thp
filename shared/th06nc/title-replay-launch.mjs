import {queueSound} from './sound-queue.mjs';
// Title playback launch 4d680. Stage indices here are zero based, as in the
// title owner; the game initializer owns the subsequent one-based conversion.
// Spell-table construction (76b90) and file loading remain caller services.
export function prepareTitleReplayLaunch(initial,decoded,stageIndex,{environment,filename,spellRecords=[],fade=null,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 const state={...initial},h=decoded.bytes,first=decoded.stageOffsets.find(p=>p!==null);
 if(first===undefined)throw Error('TH06nc replay: no recorded stage');
 if(h[6]===3){
  const spell=spellRecords.find(record=>record.id===h[8]);
  if(!spell)return {accepted:false,state};
  environment.spellPractice=true;environment.spellPracticeIndex=h[8];environment.stageIndex=spell.stageIndex;environment.difficulty=spell.difficulty;
 }else environment.spellPractice=false;
 queueSound(soundSlots,10,{disabled:soundDisabled});environment.replay=true;environment.replayFilename=filename;
 if(h[6]!==3)environment.difficulty=h[8];
 environment.character=h[7]>>>1;environment.shot=h[7]&1;environment.lifeProtection=h[6]===1;environment.lives=h[first+13];environment.bombs=h[first+14];
 if(h[6]!==3)environment.stageIndex=stageIndex|0;
 environment.replayStartStage=stageIndex|0;fade?.requestOut(0,30);state.state=26;state.frame=0;
 return {accepted:true,state};
}
