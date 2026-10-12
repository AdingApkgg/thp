import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const sha=b=>createHash('sha256').update(b).digest('hex');
const labels=['reimu-a-normal-pools-handoff-oct11','marisa-b-extra-pools-oct11','sakuya-b-extra-pools-oct11','marisa-b-normal-inputs-pools-oct11','sakuya-a-extra-inputs-pools-oct11'];
const rows=labels.map(label=>{
 const path=`artifacts/th14/campaign-replay/${label}/result.json`,bytes=readFileSync(resolve(root,path)),r=JSON.parse(bytes);
 assert.equal(r.passed,true,label);assert.equal(r.deepPools,true);assert.equal(r.phase,4);assert.equal(r.error,'');
 assert.equal(r.bulletSkippedMask,0);assert.equal(r.bulletUnsupportedNativeMask,0);
 assert.deepEqual(r.transitions.map(t=>t.stage),r.extra?[]:[2,3,4,5,6]);
 for(const name of ['bullets','shots','enemies','items','lasers','damageAreas'])assert(r.fields.includes(name+'PoolSha256'));
 for(const [name,hash] of Object.entries(r.engineBuild.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),hash,'changed engine '+name);
 assert.equal(sha(readFileSync(resolve(root,`artifacts/th14/campaign-replay/${label}/campaign.wasm`))),r.wasmSha256);
 assert.equal(sha(readFileSync(resolve(root,`artifacts/th14/campaign-replay/${label}/campaign.rpy`))),r.replaySha256);
 const ranges=[];
 for(const d of r.transitionDifferences){
  assert(['score','itemsPoolSha256'].includes(d.field));
  const entry=r.transitions.find(t=>t.stage===d.stage);assert(entry&&entry.frame<=d.frame&&d.frame<entry.frame+151,'difference outside inactive wait');
  if(d.field==='itemsPoolSha256')for(const [words,digest] of [[d.recordWords,d.record],[d.replayWords,d.replay]]){
   assert.equal(words[0],3);assert.equal((words.length-1)%16,0);
   const data=Buffer.alloc(words.length*4);words.forEach((w,i)=>data.writeUInt32LE(w,i*4));assert.equal(sha(data),digest);
  }
  const previous=ranges.findLast(x=>x.stage===d.stage&&x.field===d.field);
  if(previous&&previous.lastFrame+1===d.frame){previous.lastFrame=d.frame;++previous.frames;}
  else ranges.push({stage:d.stage,field:d.field,firstFrame:d.frame,lastFrame:d.frame,frames:1});
 }
 if(r.inputPattern){assert.equal(r.inputPatternStats.keysSeen,763);assert(r.inputPatternStats.actualBombStarts>=2);assert(r.inputPatternStats.aboveCollectionLineFrames>0);assert(r.fields.includes('bomb-active'));}
 return {label,path,reportSha256:sha(bytes),selection:r.selection,difficulty:r.difficulty,inputPattern:!!r.inputPattern,inputPatternStats:r.inputPatternStats??null,recordedFrames:r.recordedFrames,comparedFrames:r.comparedFrames,activeComparedFrames:r.activeComparedFrames??r.comparedFrames,poolHashedBytes:r.poolHashedBytes,poolPeaks:r.poolPeaks,ranges,replaySha256:r.replaySha256,engineSha256:r.engineBuild.sha256};
});
const nativePath='docs/porting/th14-campaign-handoff-native-verified-oct11.json',nativeBytes=readFileSync(resolve(root,nativePath)),native=JSON.parse(nativeBytes);
assert.equal(native.passed,true);assert.equal(native.itemFramesCompared.length,144);
assert.equal(sha(readFileSync(resolve(root,'artifacts/th14/campaign-handoff/rows.json'))),native.traceSha256);
const failedPath='artifacts/th14/campaign-replay/reimu-a-normal-pools-oct11/result.json',failedBytes=readFileSync(resolve(root,failedPath));assert.equal(JSON.parse(failedBytes).passed,false);
const report={passed:true,completeGame:false,nativeEquivalent:false,cases:rows.length,comparedFrames:rows.reduce((n,r)=>n+r.comparedFrames,0),activeComparedFrames:rows.reduce((n,r)=>n+r.activeComparedFrames,0),poolHashedBytes:rows.reduce((n,r)=>n+r.poolHashedBytes,0),rows,nativeFirstHandoff:{path:nativePath,sha256:sha(nativeBytes)},preservedStrictInactiveFailure:{path:failedPath,sha256:sha(failedBytes)},toolSha256:sha(readFileSync(import.meta.filename)),scope:'Full six-stage Normal and full Extra diagnostic campaigns: every sampled explicit numerical field in six object pools strictly identical on active replay frames; selected gameplay fields and additional bomb state on input-pattern routes. Inactive score/item differences preserved and summarized. Exact first Reimu A stage2 transient item has an independent native144-frame proof; other handoffs are not claimed to have a full native trace. No recorder chunks discarded, no added power or forced clear; fixture invulnerability is diagnostic only. Not whole native combat/replay, ANM/GPU/audio equality or natural survival.'};
writeFileSync(resolve(root,'docs/porting/th14-campaign-pools-observed-oct11.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,cases:report.cases,comparedFrames:report.comparedFrames,activeComparedFrames:report.activeComparedFrames,poolHashedBytes:report.poolHashedBytes}));
