import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {ScoreStats} from '../shared/th06nc/score-stats.mjs';
import {beginSpell,endSpell} from '../shared/th06nc/spell-state.mjs';
import {createDefaultScoreTables} from '../shared/th06nc/score-tables.mjs';
import {encodeCanonicalScore} from '../shared/th06nc/score-canonical.mjs';
import {decodeScoreFile} from '../shared/th06nc/score-file.mjs';
import {NativeRng} from '../shared/th06nc/rng.mjs';
const sources=['score-stats','spell-record','spell-state','score-stat-load','score-canonical','score-stat-chunks','score-header','score-file','score-tables','rng'].map(s=>'shared/th06nc/'+s+'.mjs'),sha=b=>createHash('sha256').update(b).digest('hex'),hashes=()=>Object.fromEntries(sources.map(p=>[p,sha(readFileSync(p))])),sourceSha256=hashes();
const fresh=()=>{const s=new ScoreStats();s.loadBoot([]);s.loadTitle([]);return s;},key='ST_ECLDATA1_SUB9_0',run=(stats,id,{replayPlayback=false,spellPractice=false,character=0,shot=0,difficulty=1}={})=>{
 const args=new Uint8Array(5+key.length);new DataView(args.buffer).setInt16(2,id,true);args.set(new TextEncoder().encode(key),4);
 const spellState={records:stats.spellRecords,captures:0,extraCaptures:0},environment={replayPlayback,spellPractice,character,shot,difficulty,score:0n};
 beginSpell({v:new DataView(new ArrayBuffer(0x10b0))},args,{spellState,environment,cancelBullets:()=>{}});endSpell({spellState,environment,bossState:{remainingSeconds:10},cancelBullets:()=>{}});
};
let stats=fresh();const digest=createHash('sha256');let checks=0;
for(let cycle=0;cycle<2;cycle++){
 for(let id=0;id<134;id++){
  const record=stats.spellRecords.get(id);assert.equal(record.bytes.buffer,stats.bytes.buffer);assert.equal(record.bytes.byteOffset,stats.cardAttack.byteOffset+id*384);
  run(stats,id,{character:id%2,shot:(id>>1)%2});assert.equal(record.attempts,cycle+1);assert.equal(record.captures,cycle+1);assert.equal(record.key,key);assert.equal(record.history[0],(id%2)*2+((id>>1)%2));
  const before=stats.cardAttack.slice();run(stats,id,{replayPlayback:true});assert.deepEqual(stats.cardAttack,before);
  run(stats,id,{spellPractice:true,character:1,shot:1,difficulty:4});assert.equal(record.practiceAttempts[19],cycle+1);assert.equal(record.practiceCaptures[19],cycle+1);checks++;
 }
 const file=encodeCanonicalScore({rng:new NativeRng(0xbeef),tables:createDefaultScoreTables(),stats}),loaded=new ScoreStats();loaded.loadBoot(decodeScoreFile(file).records);loaded.loadTitle(decodeScoreFile(file).records);assert.deepEqual(loaded.cardAttack,stats.cardAttack);digest.update(file);stats=loaded;
}
const retained=stats.spellRecords.get(19),buffer=stats.bytes.buffer;stats.loadTitle([]);assert.equal(stats.spellRecords.get(19),retained);assert.equal(retained.bytes.buffer,buffer);assert.equal(retained.attempts,2);assert.deepEqual(hashes(),sourceSha256);
const report={scope:'Host composition of real spell producer functions with shared CATK views, canonical encoding and boot/title reload. All 134 IDs over two cycles compare attempts/captures/key/history/practice counters; replay playback leaves the complete CATK pool unchanged. The producers and writer have separate native proofs. This is not natural ECL/browser gameplay or whole lifecycle equivalence.',cases:checks,stateSha256:digest.digest('hex'),sourceSha256,passed:true,completeGame:false,nativeEquivalent:false};writeFileSync('docs/porting/th06nc-spell-persistence-verified.json',JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:checks}));
