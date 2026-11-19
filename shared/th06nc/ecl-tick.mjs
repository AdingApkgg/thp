import {advanceEclMotion} from './ecl-motion.mjs';
import {finishEclEnemyFrame} from './ecl-enemy-tail.mjs';
// One ECL enemy update, before the world manager integrates position/collisions.
export function tickEclEnemy(dispatch,options={}){
 const result=dispatch.runDue(options);
 if(!result.deleted&&!result.debugStopped){advanceEclMotion(dispatch.enemy,dispatch.services);finishEclEnemyFrame(dispatch.enemy,result.nextOffset,dispatch.services);}
 return result;
}
