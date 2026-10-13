// Reuse a fully source-bound diagnostic build; each input gets a fresh module.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const label=process.argv[2];assert(/^[a-z0-9-]{1,64}$/.test(label));
const dir=resolve(root,'artifacts/th14/sanitized-replay',label),sha=b=>createHash('sha256').update(b).digest('hex');
const compile=JSON.parse(readFileSync(resolve(dir,'compile-build.json')));
for(const [name,digest] of Object.entries(compile.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),digest,name);
for(const [path,digest] of Object.entries(compile.objectSha256))assert.equal(sha(readFileSync(path)),digest,path);
assert(compile.flags.includes('-fsanitize=address,undefined')&&compile.flags.includes('-fno-sanitize-recover=all'));
const loaderPath=resolve(dir,'sanitized.mjs'),wasm=readFileSync(resolve(dir,'sanitized.wasm'));
const create=(await import(pathToFileURL(loaderPath).href)).default;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);
const cases=[];
for(const [file,playbackLabel] of [
 ['th14_udzp01.rpy','zps-reimua-lunatic-release-area-oct14'],['th14_udzp02.rpy','zps-reimub-lunatic-release-area-oct14'],['th14_udzp07.rpy','zps-reimua-extra-release-area-oct14']]){
 const expected=JSON.parse(readFileSync(resolve(root,'artifacts/th14/public-replay-playback',playbackLabel,'report.json')));
 assert.deepEqual(expected.sourceHashes,compile.sourceHashes);
 const expectedFrames=expected.frames,expectedStage=expected.stage,expectedEnded=expected.candidatePlaybackEnded;
 const errors=[],module=await create({wasmBinary:wasm,print:()=>{},printErr:line=>{errors.push(line);console.error(line);}});
 const names=['allocate','open_archive','public_replay_begin','tick','draw','public_replay_clock','phase','public_replay_status','error'];
 const c=Object.fromEntries(names.map(name=>[name,module['_'+name]??module[name]]));
 for(const name of names)assert.equal(typeof c[name],'function',name);
 const upload=b=>{const p=c.allocate(b.length);module.HEAPU8.set(b,p);return p;};
 const replayPath=resolve(root,'artifacts/th14/public-replay-reference',file),replay=readFileSync(replayPath);
 const source=JSON.parse(readFileSync(replayPath.replace(/\.rpy$/,'-source.json')));assert.equal(sha(replay),source.sha256);
 assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.public_replay_begin(upload(replay),replay.length),1);
 let frames=0;
 for(let frame=1;frame<=200000;frame++){
  assert.equal(c.tick(0),1,file+' tick '+frame);assert.equal(c.draw(),1,file+' draw '+frame);assert.equal(c.public_replay_clock(frame/60),1);frames=frame;
  if(frame%24000===0)console.log(JSON.stringify({file,instrumentedFrames:frame,stage:c.public_replay_status(0)}));
  if([3,4,5].includes(c.phase()))break;
 }
 assert(!errors.some(line=>/AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer/.test(line)));
 assert.equal(frames,expectedFrames);assert.equal(c.public_replay_status(0),expectedStage);assert.equal(c.phase(),4);
 assert.equal(!!c.public_replay_status(3),!expectedEnded);assert.equal(c.public_replay_status(5),0);assert.equal(c.public_replay_status(6),0);
 cases.push({file,replaySha256:sha(replay),frames,stage:expectedStage,sanitizerPassed:true,candidatePlaybackEnded:expectedEnded,gameOver:!expectedEnded,errors});
 console.log(JSON.stringify(cases.at(-1)));
}
const report={sanitizerMatrixVerified:true,completeGame:false,nativeEquivalent:false,cases,
 sourceHashes:compile.sourceHashes,sanitizerFlags:compile.flags,compileBuildSha256:sha(readFileSync(resolve(dir,'compile-build.json'))),
 loaderSha256:sha(readFileSync(loaderPath)),wasmSha256:sha(wasm),wasmBytes:wasm.length,
 fixtureSha256:sha(readFileSync(resolve(rt,'tests/cpp/th14-public-replay-physical-fixture.cpp'))),toolSha256:sha(readFileSync(import.meta.filename)),
 scope:'Each intact independent public input executes in a fresh instance of the same fully source/object-bound production ASAN/UBSan build. Nonrecovering memory/math checks pass for the executed paths; the retained ReimuA Lunatic GameOver is not promoted to a clear. Instrumented playback is not independent original equivalence, leak teardown, browser graphics/audio/storage, all modes or whole-game1:1.'};
writeFileSync(resolve(root,`docs/porting/th14-sanitized-input-parity-matrix-${label}-observed-oct14.json`),JSON.stringify(report,null,2)+'\n');
