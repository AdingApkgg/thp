import {findSpellPractice} from './spell-practice-table.mjs';

// Spell branch of timeline phase 36260..363bd. Initial ECL execution and its
// ordinary spawn bookkeeping belong to EnemyPool, not to the stage timeline.
export function spawnSpellPracticeEnemy(pool,table,environment=pool.environment){
 if(!environment.spellPractice||environment.spellEnemyStarted)return null;
 if(!Array.isArray(table))throw Error('TH06nc: spell-practice catalog required');
 const row=findSpellPractice(table,environment.spellPracticeIndex);if(!row)return null;
 let slot=0;while(slot<256&&(pool.storage[slot*0x10b0+0xbc]&128))slot++;
 if(slot===256){environment.spellEnemyStarted=true;return null;}
 const entry=pool.spawn({sub:(row.subroutine<<16)>>16,position:[192,-64,0],item:-2,score:200000});
 environment.spellEnemyStarted=true;return entry;
}
