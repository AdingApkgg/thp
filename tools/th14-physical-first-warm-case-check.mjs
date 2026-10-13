// Declare warm-mode provenance around the physical-order raw32 comparison.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),option=n=>process.argv[process.argv.indexOf(n)+1],sha=b=>createHash('sha256').update(b).digest('hex');
assert(process.argv.includes('--native')&&process.argv.includes('--label'));
const nativePath=resolve(root,option('--native')),bytes=readFileSync(nativePath),native=JSON.parse(bytes),init=native.caseInitialization;
assert.equal(native.childGameStateOverrides,1);assert.equal(native.ordinaryMenuLoaderVerified,false);
assert.equal(init.address,'0x4f58b8');assert.equal(init.before,0x40);assert.equal(init.after,0);assert.equal(init.wordWrites,1);assert.equal(init.replayManagerMode,1);
assert(init.afterReadOnlyBootstrap&&init.beforeFirstPlayerInstruction);
assert.equal(sha(readFileSync(resolve(root,'tools/th14-native-stored-bootstrap-capture.py'))),native.warmReplayCaptureToolSha256);
await import('./th14-physical-replay-reference-trace-check.mjs');
const path=resolve(root,`docs/porting/th14-physical-replay-native-trace-${option('--label')}-observed-oct13.json`),report=JSON.parse(readFileSync(path));
assert.equal(report.nativeTraceSha256,sha(bytes));assert(report.physicalInvocationOrder);
report.nativeCaseInitialization=init;report.nativeWarmCaptureToolSha256=native.warmReplayCaptureToolSha256;
report.physicalWarmWrapperSha256=sha(readFileSync(import.meta.filename));report.ordinaryMenuLoaderVerified=false;
report.scope+=' Native starts from pure flag40 and clears attract bit40 once after the untouched bootstrap. This declared initialization and a timed-out native capture do not become ordinary menu/startup, uninterrupted transition or complete-game certification.';
writeFileSync(path,JSON.stringify(report,null,2)+'\n');
