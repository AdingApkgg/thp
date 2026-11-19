import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {advanceClearedProgress,markClearedCompletion} from '../shared/th06nc/cleared-progress.mjs';
import {clearedUnlocks} from '../shared/th06nc/cleared-unlocks.mjs';
import {ScoreStats} from '../shared/th06nc/score-stats.mjs';
import {encodeCanonicalScore} from '../shared/th06nc/score-canonical.mjs';
import {decodeScoreFile} from '../shared/th06nc/score-file.mjs';
import {createDefaultScoreTables} from '../shared/th06nc/score-tables.mjs';
import {NativeRng} from '../shared/th06nc/rng.mjs';
const sources=['cleared-progress','cleared-unlocks','score-stats','score-stat-load','spell-record','score-canonical','score-file','score-header','score-stat-chunks','score-tables','rng'].map(s=>'shared/th06nc/'+s+'.mjs'),sha=b=>createHash('sha256').update(b).digest('hex'),hashes=()=>Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))])),sourceSha256=hashes(),digest=createHash('sha256');let cases=0;
for(let profile=0;profile<4;profile++)for(let difficulty=0;difficulty<5;difficulty++)for(const lifeProtection of [false,true])for(const deathCount of [0,5,6])for(const continuesUsed of [0,1]){
 const stats=new ScoreStats();stats.loadBoot([]);stats.loadTitle([]);const e={character:profile>>1,shot:profile&1,difficulty,lifeProtection,deathCount,continuesUsed};
 for(let stageIndex=0;stageIndex<=6;stageIndex++)assert.equal(advanceClearedProgress(stats.cleared,{...e,stageIndex}),stageIndex+1);
 const p=profile*24+difficulty,eligible=continuesUsed===0&&(!lifeProtection||deathCount<=5);assert.equal(stats.cleared[p+17],6);assert.equal(stats.cleared[p+12],continuesUsed===0&&lifeProtection&&deathCount<=5?6:1);
 const result=markClearedCompletion(stats.cleared,e);assert.deepEqual(result,{alreadyCleared:false,restricted:!eligible});assert.equal(stats.cleared[p+17],99);assert.equal(stats.cleared[p+12]===99,eligible);assert.equal(markClearedCompletion(stats.cleared,e).alreadyCleared,true);
 const file=encodeCanonicalScore({rng:new NativeRng(0xbeef),tables:createDefaultScoreTables(),stats}),loaded=new ScoreStats(),records=decodeScoreFile(file).records;loaded.loadBoot(records);loaded.loadTitle(records);assert.deepEqual(loaded.cleared,stats.cleared);const unlock=clearedUnlocks(loaded.cleared),expected=eligible&&difficulty>=1&&difficulty<=3;assert.equal(unlock.extraAvailable,expected);assert.equal(unlock.extraUnlockedShots[profile>>1][profile&1],expected);digest.update(file);cases++;
}
assert.deepEqual(hashes(),sourceSha256);const report={scope:'Host CLRD producer to canonical file to boot/title load and Extra unlock composition. All profiles/difficulties/protection/death/continue combinations preserve full CLRD bytes and repeat-clear status. Native producer and unlock primitives have separate original-code proofs. Controlled calls are not a natural game clear, ending scene, or full browser lifecycle.',cases,stateSha256:digest.digest('hex'),sourceSha256,passed:true,completeGame:false,nativeEquivalent:false};writeFileSync('docs/porting/th06nc-cleared-persistence-verified.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases}));
