// Compile the merged core once with nonrecovering ASAN/UBSan, then run four
// independent intact inputs in fresh instances against fresh headless results.
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname, '..'), rt=resolve(root, 'runtimes/th12/th12_web');
const sdk=resolve(root, 'runtimes/th12/tools/emsdk'), sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const [label, ...playbackLabels]=process.argv.slice(2);
assert(/^[a-z0-9-]{1,80}$/.test(label) && playbackLabels.length===4, 'Pass a fresh label and four fresh production playback labels');
const out=resolve(root, 'artifacts/th14/staged-loader-production-sanitized', label);
assert(!existsSync(out), 'Evidence output must be new');
const buildPath=resolve(root, 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json');
const engineBytes=readFileSync(buildPath), engine=JSON.parse(engineBytes);
for(const [path, hash] of Object.entries(engine.sourceHashes)) assert.equal(sha(readFileSync(resolve(rt, path))), hash, path);
assert(readFileSync(resolve(rt, 'cpp/game/GameSession.hpp'), 'utf8').includes('stage_load_clock'));
const inputs=['th14_udzp01.rpy', 'th14_udzp02.rpy', 'th14_udzp07.rpy', 'th14_udzp05.rpy'];
const expected=playbackLabels.map((name, index)=>{
  assert(/^[a-z0-9-]{1,80}$/.test(name));
  const directory=resolve(root, 'artifacts/th14/staged-loader-production-playback', name);
  const bytes=readFileSync(resolve(directory, 'report.json')), report=JSON.parse(bytes);
  assert(report.productionPlaybackVerified && report.candidatePlaybackEnded);
  assert.deepEqual(report.sourceHashes, engine.sourceHashes);
  assert.equal(report.replaySha256, sha(readFileSync(resolve(root, 'artifacts/th14/public-replay-reference', inputs[index]))));
  assert.equal(report.selectedStateSha256, sha(readFileSync(resolve(directory, 'selected-state.u32'))));
  assert.equal(report.callbackActiveSha256, sha(readFileSync(resolve(directory, 'callback-active.u8'))));
  return {directory, report, reportSha256:sha(bytes)};
});
const objects=resolve(out, 'objects'); mkdirSync(objects, {recursive:true});
writeFileSync(resolve(out, 'engine-build.json'), engineBytes);
const fixtureDependencyHashes=expected[0].report.fixtureDependencyHashes;
assert(fixtureDependencyHashes && Object.keys(fixtureDependencyHashes).length>3);
for(const item of expected)assert.deepEqual(item.report.fixtureDependencyHashes,fixtureDependencyHashes);
for(const [name,hash]of Object.entries(fixtureDependencyHashes))assert.equal(sha(readFileSync(resolve(root,name))),hash,name);
const python=resolve(sdk, 'python', readdirSync(resolve(sdk, 'python')).sort().reverse()
  .find(name=>existsSync(resolve(sdk, 'python', name, 'python.exe'))), 'python.exe');
const env={...process.env, EM_CONFIG:resolve(sdk, '.emscripten'), EMSDK:sdk, EMSDK_PYTHON:python,
  EMCC_CORES:'4', TEMP:out, TMP:out, TMPDIR:out};
const flags=['-O1', '-g', '-std=c++17', '-ffp-contract=off', '-fno-strict-aliasing',
  '-fno-exceptions', '-fno-rtti', '-DPORT_TITLE=14', '-fsanitize=address,undefined', '-fno-sanitize-recover=all'];
const run=args=>new Promise((accept,reject)=>{
  const child=spawn(python, [resolve(sdk, 'upstream/emscripten/emcc.py'), ...args], {cwd:rt, env, windowsHide:true, stdio:['ignore','pipe','pipe']});
  let log=''; for(const stream of [child.stdout,child.stderr]) stream.on('data', bytes=>log+=bytes);
  child.on('error', reject); child.on('exit', code=>code?reject(Error(log)):accept());
});
const compiled=new Array(engine.sources.length); let cursor=0;
await Promise.all(Array.from({length:4}, async()=>{while(cursor<engine.sources.length){
  const index=cursor++, name=engine.sources[index], object=resolve(objects, name.replaceAll('/', '_')+'.o');
  await run([...flags, '-c', name, '-o', object]); compiled[index]=object;
}}));
const fixtureNames=['th14-public-replay-physical-fixture.cpp', 'th14-custom-replay-reference-fixture.cpp', 'th14-session-reference-fixture.cpp'];
const fixtureHashes=Object.fromEntries(fixtureNames.map(name=>[name,sha(readFileSync(resolve(rt,'tests/cpp',name)))]));
const fixture=resolve(out, 'sanitized-clock-fixture.cpp');
writeFileSync(fixture, `#include "${resolve(rt, 'tests/cpp', fixtureNames[0]).replaceAll('\\','/')}"\n`+
  'static u64 sanitized_clock_ns=0;\n'+
  'API(sanitized_clock_begin) void sanitized_clock_begin(){sanitized_clock_ns=0;session.stage_load_clock=[](){return sanitized_clock_ns;};}\n'+
  'API(sanitized_clock_set) void sanitized_clock_set(u32 low,u32 high){sanitized_clock_ns=(u64(high)<<32)|low;}\n'+
  'API(sanitized_capture_retire) void sanitized_capture_retire(){session.animations.retire_deferred_captures_without_target();}\n');
const loader=resolve(out, 'sanitized.mjs');
await run([...flags, fixture, ...compiled, '--no-entry', '-sDEFAULT_TO_CXX=1', '-sMODULARIZE=1',
  '-sEXPORT_ES6=1', '-sENVIRONMENT=node', '-sALLOW_MEMORY_GROWTH=1', '-sINITIAL_MEMORY=536870912',
  '-sMAXIMUM_MEMORY=2147483648', '-sSTACK_SIZE=1048576', '-sINVOKE_RUN=0', '-sASSERTIONS=1',
  '-sEXIT_RUNTIME=0', '-sINCOMING_MODULE_JS_API=wasmBinary,print,printErr', '-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPU32', '-o', loader]);
const wasm=readFileSync(resolve(out, 'sanitized.wasm')), create=(await import(pathToFileURL(loader).href)).default;
const target=JSON.parse(readFileSync(resolve(root, 'runtimes/th14/target.json'))), archive=readFileSync(target.dataArchives['th14.dat'].path);
const cases=[];
for(let index=0; index<inputs.length; ++index){
  const file=inputs[index], errors=[], module=await create({wasmBinary:wasm, print:()=>{}, printErr:line=>{errors.push(line);console.error(line);}});
  const names=['allocate','open_archive','public_replay_begin','tick','draw','public_replay_clock','phase','public_replay_status',
    'public_replay_observations','public_replay_observed_active','reference_data','error','sanitized_clock_begin','sanitized_clock_set','sanitized_capture_retire'];
  const c=Object.fromEntries(names.map(name=>[name,module['_'+name]??module[name]]));
  for(const name of names) assert.equal(typeof c[name], 'function', name);
  const upload=bytes=>{const pointer=c.allocate(bytes.length);module.HEAPU8.set(bytes,pointer);return pointer;};
  const replay=readFileSync(resolve(root, 'artifacts/th14/public-replay-reference', file));
  assert.equal(c.open_archive(upload(archive),archive.length),1); c.sanitized_clock_begin();
  assert.equal(c.public_replay_begin(upload(replay),replay.length),1);
  const rows=[],active=[];let frames=0,observations=c.public_replay_observations();
  for(let frame=1;frame<=200000;++frame){
    const now=BigInt(frame)*1000000000n/60n;
    c.sanitized_clock_set(Number(now&0xffffffffn),Number(now>>32n));
    assert.equal(c.tick(0),1,file+' tick '+frame);assert.equal(c.draw(),1,file+' draw '+frame);
    c.sanitized_capture_retire();
    assert.equal(c.public_replay_clock(frame/60),1);frames=frame;
    const next=c.public_replay_observations();assert(next===observations||next===observations+1);
    if(next===observations+1){rows.push(...new Uint32Array(module.HEAPU8.buffer,c.reference_data(),32));active.push(c.public_replay_observed_active());}
    observations=next;
    if([3,4,5].includes(c.phase()))break;
    if(frame%24000===0)console.log(JSON.stringify({file,frames:frame,stage:c.public_replay_status(0)}));
  }
  const state=Buffer.from(new Uint32Array(rows).buffer),activity=Buffer.from(active), wanted=expected[index];
  // Store complete instrumented observations before asserting parity.
  writeFileSync(resolve(out,file+'.state.u32'),state);writeFileSync(resolve(out,file+'.active.u8'),activity);
  assert.equal(sha(state),wanted.report.selectedStateSha256);assert.equal(sha(activity),wanted.report.callbackActiveSha256);
  assert.equal(frames,wanted.report.frames);assert.equal(c.phase(),4);assert.equal(c.public_replay_status(3),0);
  assert.equal(c.public_replay_status(5),0);assert.equal(c.public_replay_status(6),0);
  assert(!errors.some(line=>/AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer/.test(line)));
  cases.push({file,frames,stage:c.public_replay_status(0),sanitizerPassed:true,allRaw32WordsEqual:true,
    selectedStateSha256:sha(state),callbackActiveSha256:sha(activity),playbackReportSha256:wanted.reportSha256,errors});
  console.log(JSON.stringify(cases.at(-1)));
}
for(const [path,hash]of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,path))),hash,path);
for(const [name,hash]of Object.entries(fixtureDependencyHashes))assert.equal(sha(readFileSync(resolve(root,name))),hash,name);
const report={sanitizerMatrixVerified:true,completeGame:false,nativeEquivalent:false,cases,
  sourceHashes:engine.sourceHashes,objectSha256:Object.fromEntries(compiled.map((path,index)=>[engine.sources[index],sha(readFileSync(path))])),
  sanitizerFlags:flags,engineBuildSha256:sha(engineBytes),fixtureHashes,fixtureDependencyHashes,generatedFixtureSha256:sha(readFileSync(fixture)),
  loaderSha256:sha(readFileSync(loader)),wasmSha256:sha(wasm),wasmBytes:wasm.length,archiveSha256:sha(archive),toolSha256:sha(readFileSync(import.meta.filename)),
  scope:'Four fresh instrumented instances of the merged production core, with explicit controlled60Hz clock and every physical callback compared to fresh same-source uninstrumented results. Nonrecovering memory/math checks cover executed paths. No native scheduling, actual SDL/GPU upload, cancel teardown, pixel/audio/browser storage or whole-game equality claim.'};
writeFileSync(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({sanitizerMatrixVerified:true,cases:cases.length,wasmBytes:wasm.length}));
