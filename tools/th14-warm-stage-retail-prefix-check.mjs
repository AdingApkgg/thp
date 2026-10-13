// Reuse the frozen physical-process comparison, preserving all differences.
// Explicitly bind and describe the warm Replay mode initialization separately.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),option=name=>process.argv[process.argv.indexOf(name)+1],sha=b=>createHash('sha256').update(b).digest('hex');
assert(process.argv.includes('--native')&&process.argv.includes('--label'));
const nativePath=resolve(root,option('--native')),nativeBytes=readFileSync(nativePath),native=JSON.parse(nativeBytes);
const init=native.caseInitialization;
assert.equal(native.childGameStateOverrides,1);assert.equal(native.ordinaryMenuLoaderVerified,false);
assert.equal(init.address,'0x4f58b8');assert.equal(init.before,0x44);assert.equal(init.after,4);assert.equal(init.wordWrites,1);
assert.equal(init.afterReadOnlyBootstrap,true);assert.equal(init.beforeFirstPlayerInstruction,true);assert.equal(init.replayManagerMode,1);
assert.equal(sha(readFileSync(resolve(root,'tools/th14-native-stored-stage-bootstrap-capture.py'))),native.warmReplayCaptureToolSha256);
await import('./th14-natural-replay-reference-trace-check.mjs');
const path=resolve(root,`docs/porting/th14-natural-replay-native-trace-${option('--label')}-observed-oct13.json`),report=JSON.parse(readFileSync(path));
assert.equal(report.nativeTraceSha256,sha(nativeBytes));
report.warmCaseWrapperSha256=sha(readFileSync(import.meta.filename));report.nativeCaseInitialization=init;
report.nativeWarmCaptureToolSha256=native.warmReplayCaptureToolSha256;
report.ordinaryMenuLoaderVerified=false;
report.scope='Independent hidden retail child versus current production core for an explicitly initialized warm Replay case. The native child clears one attract-mode word after the untouched later-stage bootstrap, retaining flag4; no stock/health/input/RNG/time overrides. All raw 32 state words and captured object differences retained, without reseeding or resynchronization. This includes ordinary collision and can expose desynchronization/GameOver, but is not unmodified ordinary menu/loader startup, an uninterrupted transition, a natural retail clear, full six-stage Replay, HAL pixels/audio or browser storage certification.';
writeFileSync(path,JSON.stringify(report,null,2)+'\n');
