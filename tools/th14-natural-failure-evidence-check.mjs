import assert from 'node:assert/strict';import {readFileSync,writeFileSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),sha=b=>createHash('sha256').update(b).digest('hex'),evidence={};
const track=p=>{const b=readFileSync(resolve(root,p));evidence[p]={bytes:b.length,sha256:sha(b)};return b;},json=p=>JSON.parse(track(p));
const results=[];
for(const label of ['normal-sakuyaa-live-bullet','normal-sakuyaa-geometry-risk']){
 const base='artifacts/th14/natural-input/'+label+'/',r=json(base+'failure-diagnostics/report.json'),original=json(base+'report.json');
 assert(r.recordingByteExact&&!r.productionChanged&&!r.gameplayStateWritten&&!r.completeGame&&!r.nativeEquivalent);assert.equal(r.frames,original.frames);assert.equal(r.terminalPhase,original.phase);
 assert.equal(sha(track(base+'held-keys.u32')),r.inputsSha256);assert.equal(r.inputsSha256,original.inputsSha256);assert.equal(sha(track(base+'ordinary-input.rpy')),r.replaySha256);assert.equal(r.replaySha256,original.replaySha256);
 assert.equal(sha(track(base+'failure-diagnostics/failure.wasm')),r.wasmSha256);assert.equal(sha(track('tools/th14-natural-failure-check.mjs')),r.toolSha256);
 assert.equal(sha(track('runtimes/th12/th12_web/tests/cpp/th14-natural-failure-fixture.cpp')),r.fixtureSha256);assert.equal(sha(track('runtimes/th12/th12_web/tests/cpp/th14-natural-input-fixture.cpp')),r.includedFixtureSha256);
 for(const [p,h] of Object.entries(r.engineBuild.sourceHashes))assert.equal(sha(track('runtimes/th12/th12_web/'+p)),h,p);
 const last=r.events.at(-1);assert.equal(last.before.length,32);assert.equal(last.before[0],6);assert.equal(last.before[3],4);assert.equal(last.after[3],2);assert(last.before[24]<last.before[26]);
 const float=word=>{const b=Buffer.alloc(4);b.writeUInt32LE(word);return b.readFloatLE();};
 results.push({label,frames:r.frames,recordingByteExact:true,lastDeathFrame:last.inputFrame,bossHealth:last.before[12],phaseClock:last.before[24],phaseTimeout:last.before[26],playerRadius:float(last.before[30]),playerScale:float(last.before[29])});
}
const phase=json('docs/porting/th14-survival-phase-verified-oct13.json');assert(phase.passed&&!phase.completeGame&&!phase.nativeEquivalent);assert.equal(phase.cases,84);assert.equal(sha(track('artifacts/th14/survival-phase-native.json')),phase.nativeProofSha256);
for(const [p,h] of Object.entries(phase.sourceHashes))assert.equal(sha(track('runtimes/th12/th12_web/'+p)),h,p);for(const [p,h] of Object.entries(phase.toolHashes))assert.equal(sha(track(p)),h,p);
const report={diagnosticEvidenceVerified:true,productionChanged:false,completeGame:false,nativeEquivalent:false,results,nativePhaseUnitCases:phase.cases,evidence,scope:'Verify hashes and explicit failure telemetry constraints for ordinary input reproduction with byte-exact recorder checks; phase clock is below timeout at both terminal deaths. Retail machine-code phase boundary unit comparison is separate. Does not independently identify the colliding object, repeat every diagnostic state word, or prove Native full campaign, graphics/audio or browser storage.'};writeFileSync(resolve(root,'docs/porting/th14-natural-normal-failure-verified-oct13.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({diagnosticEvidenceVerified:true,results,nativePhaseUnitCases:phase.cases}));
