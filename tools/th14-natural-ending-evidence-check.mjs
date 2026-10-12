import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),evidence={};
const sha=b=>createHash('sha256').update(b).digest('hex');
const track=p=>{const b=readFileSync(resolve(root,p));evidence[p]={bytes:b.length,sha256:sha(b)};return b;};
const report=JSON.parse(track('artifacts/th14/natural-input/easy-sakuyaa/post-ending/report.json'));
assert(report.passed&&!report.completeGame&&!report.nativeEquivalent&&!report.productionChanged);
assert(!report.invulnerabilityOverride&&!report.forcedProgression);
assert.equal(report.naturalInputFrames,92137);assert.equal(report.endingIndex,5);
assert.equal(report.endingFrames,3737);assert.equal(report.finalPhase,0);assert.equal(report.titleScreen,14);
for(const [field,path] of [
 ['wasmSha256','artifacts/th14/natural-input/easy-sakuyaa/post-ending/ending.wasm'],
 ['inputsSha256','artifacts/th14/natural-input/easy-sakuyaa/held-keys.u32'],
 ['fixtureSha256','runtimes/th12/th12_web/tests/cpp/th14-natural-ending-fixture.cpp'],
 ['includedFixtureSha256','runtimes/th12/th12_web/tests/cpp/th14-natural-input-fixture.cpp'],
 ['engineBuildSha256','runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'],
 ['toolSha256','tools/th14-natural-ending-check.mjs']])assert.equal(report[field],sha(track(path)),path);
const engine=JSON.parse(track('runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'));
for(const [p,h] of Object.entries(engine.sourceHashes))assert.equal(sha(track('runtimes/th12/th12_web/'+p)),h,p);
const fixture=track('runtimes/th12/th12_web/tests/cpp/th14-natural-ending-fixture.cpp').toString();
assert(!fixture.includes('finish_stage('));
const producer=track('tools/th14-natural-ending-check.mjs').toString();
assert(!/c\.(?:combat_tick|finish_stage)\(/.test(producer));
const target=JSON.parse(track('runtimes/th14/target.json'));
assert.equal(report.archiveSha256,sha(readFileSync(target.dataArchives['th14.dat'].path)));
const out={...report,sourceFilesVerified:Object.keys(engine.sourceHashes).length,evidence,evidenceCheckerSha256:sha(readFileSync(import.meta.filename)),scope:report.scope+' Independent integrity binding only; original raw artifacts remain local.'};
writeFileSync(resolve(root,'docs/porting/th14-natural-ending-verified-oct12.json'),JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({passed:true,endingIndex:out.endingIndex,endingFrames:out.endingFrames,titleScreen:out.titleScreen,sourceFilesVerified:out.sourceFilesVerified}));
