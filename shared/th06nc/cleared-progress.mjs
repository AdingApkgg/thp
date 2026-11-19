const profile=e=>(e.character&255)*2+(e.shot&255);
function offset(bytes,e){if(!(bytes instanceof Uint8Array)||bytes.length!==96)throw Error('TH06nc CLRD: invalid owner');const p=profile(e)*24+(e.difficulty|0);if(p<0||p+17>=bytes.length)throw Error('TH06nc CLRD: invalid index');return p;}
// Native stage-init prefix 3af27..3afe5. Stage increments even when progress
// recording is disabled. Caller owns the actual new-stage initialization.
export function advanceClearedProgress(bytes,e){
 const stage=e.stageIndex|0,next=(stage+1)|0;
 if(e.replayPlayback||e.spellPractice)return next;
 const p=offset(bytes,e);
 if(((e.continuesUsed??0)&255)===0&&e.lifeProtection&&(e.deathCount|0)<=5&&bytes[p+12]<stage)bytes[p+12]=stage&255;
 if(bytes[p+17]<stage)bytes[p+17]=stage&255;
 return next;
}
// Native ending-init 2c9ef..2caa6. The caller owns the decision to enter this
// ending owner; this block itself has no playback/practice guard.
export function markClearedCompletion(bytes,e){
 const p=offset(bytes,e),eligible=((e.continuesUsed??0)&255)===0&&(!e.lifeProtection||(e.deathCount|0)<=5);
 const alreadyCleared=bytes[p+(eligible?12:17)]===99;
 if(eligible)bytes[p+12]=99;
 bytes[p+17]=99;
 return {alreadyCleared,restricted:!eligible};
}
