import {queueSound} from './sound-queue.mjs';
const U=n=>BigInt.asUintN(64,BigInt(n??0));
export const scoreExtendThresholds=[10000000n,20000000n,40000000n,60000000n,1900000000n];
// Game owner 3a626..3a7bd, before its frame counter publication.
// continueState retains the existing environment name for owner d292;
// this same byte is the score-extend index and uses -1 to disable extends.
export function advanceScore(environment,{soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 let score=U(environment.score),shown=U(environment.displayScore),step=U(environment.scoreDisplayStep);
 if(score>=10000000000n){score=9999999990n;environment.score=score;}
 if(shown===score)return;
 if(shown>score){score=shown;environment.score=score;}
 const difference=U(score-shown),candidate=difference>>5n,rate=(candidate>=78910n?78910n:candidate<10n?10n:candidate)/10n*10n;
 if(step<rate)step=rate;
 if(U(shown+step)>score)step=difference;
 shown=U(shown+step);if(shown>=score){step=0n;shown=score;}
 environment.displayScore=shown;environment.scoreDisplayStep=step;
 const index=(environment.continueState??0)&255;
 if(!environment.scoreExtendsDisabled&&index<=4&&scoreExtendThresholds[index]<=shown){
  if(environment.lifeProtection){environment.deathCount=((environment.deathCount??0)-1)|0;queueSound(soundSlots,28,{disabled:soundDisabled});}
  else if(((environment.lives??0)<<24>>24)<8){environment.lives=((environment.lives??0)+1)&255;queueSound(soundSlots,28,{disabled:soundDisabled});}
  environment.inputFlags=((environment.inputFlags??0)&~1)|2;environment.continueState=(index+1)&255;
 }
 if(U(environment.highScore)<shown)environment.highScore=shown;
}
