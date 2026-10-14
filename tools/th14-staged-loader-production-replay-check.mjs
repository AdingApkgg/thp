// Fresh production replay evidence after the staged loader is merged.
// A declared 60 Hz monotonic test clock replaces wall time, never retail timing.
import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdirSync, existsSync, copyFileSync} from 'node:fs';
import {resolve, dirname, relative} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';

const root = resolve(import.meta.dirname, '..');
const rt = resolve(root, 'runtimes/th12/th12_web');
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const [replayArgument, label] = process.argv.slice(2);
assert(replayArgument && /^[a-z0-9-]{1,80}$/.test(label), 'Pass a replay path and a fresh result label');
const out = resolve(root, 'artifacts/th14/staged-loader-production-playback', label);
assert(!existsSync(out), 'Evidence output must be new');
const buildPath = resolve(root, 'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json');
const buildBytes = readFileSync(buildPath), build = JSON.parse(buildBytes);
assert.equal(build.title, 14);
assert.equal(sha(readFileSync(resolve(root, 'runtimes/th13/th13_web/artifacts/cpp/engine-th14.wasm'))), build.sha256);
for (const [name, expected] of Object.entries(build.sourceHashes))
  assert.equal(sha(readFileSync(resolve(rt, name))), expected, `Stale engine source: ${name}`);
assert(readFileSync(resolve(rt, 'cpp/game/GameSession.hpp'), 'utf8').includes('stage_load_clock'),
  'Run only after the staged loader is in production');
const replayPath = resolve(root, replayArgument), replay = readFileSync(replayPath);
const metadataPath = replayPath.replace(/\.rpy$/, '-source.json');
const metadataBytes = readFileSync(metadataPath), metadata = JSON.parse(metadataBytes);
assert.equal(sha(replay), metadata.sha256);
mkdirSync(out, {recursive:true});
writeFileSync(resolve(out, 'engine-build.json'), buildBytes);
for (const name of Object.keys(build.sourceHashes)) {
  const destination=resolve(out, 'source', name);
  mkdirSync(resolve(destination, '..'), {recursive:true});
  copyFileSync(resolve(rt, name), destination);
}
const fixtureNames = ['th14-public-replay-physical-fixture.cpp',
  'th14-custom-replay-reference-fixture.cpp', 'th14-session-reference-fixture.cpp'];
const fixtureHashes = Object.fromEntries(fixtureNames.map(name => [name,
  sha(readFileSync(resolve(rt, 'tests/cpp', name)))]));
const fixtureDependencyHashes={};
function bindFixture(path){
  const name=relative(root,path).replaceAll('\\','/');
  assert(!name.startsWith('../'), 'Fixture dependency leaves the workspace');
  if(fixtureDependencyHashes[name])return;
  const bytes=readFileSync(path);fixtureDependencyHashes[name]=sha(bytes);
  const archived=resolve(out,'fixture-source',name);mkdirSync(dirname(archived),{recursive:true});writeFileSync(archived,bytes);
  for(const match of bytes.toString('utf8').matchAll(/^\s*#\s*include\s*"([^"]+)"/gm))
    bindFixture(resolve(dirname(path),match[1]));
}
bindFixture(resolve(rt,'tests/cpp',fixtureNames[0]));
const fixture = resolve(out, 'production-clock-fixture.cpp');
writeFileSync(fixture, `#include "${resolve(rt, 'tests/cpp', fixtureNames[0]).replaceAll('\\', '/')}"\n` +
  'static u64 production_test_clock_ns=0;\n' +
  'API(production_clock_begin) void production_clock_begin(){production_test_clock_ns=0;session.stage_load_clock=[](){return production_test_clock_ns;};}\n' +
  'API(production_clock_set) void production_clock_set(u64 now){production_test_clock_ns=now;}\n' +
  'API(production_capture_retire) void production_capture_retire(){session.animations.retire_deferred_captures_without_target();}\n');
const objectRoot = resolve(root, 'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
// Link only this build\'s listed objects; stale objects in the cache are excluded.
const headerNames=Object.keys(build.sourceHashes).filter(name=>!name.endsWith('.cpp')).sort();
const headersKey=sha(headerNames.map(name=>name+' '+build.sourceHashes[name]).join('\n'));
mkdirSync(resolve(out, 'objects'));
const objects = build.sources.map(name => {
  const path=resolve(objectRoot, name.replaceAll('/', '_')+'.o');
  const expectedKey=sha(JSON.stringify([build.compileFlags, headersKey, build.sourceHashes[name]]));
  assert.equal(readFileSync(path+'.key', 'utf8'), expectedKey, `Stale engine object: ${name}`);
  const archived=resolve(out, 'objects', name.replaceAll('/', '_')+'.o');
  copyFileSync(path, archived);
  return archived;
});
const objectHashes = Object.fromEntries(objects.map((path, index) => [build.sources[index], sha(readFileSync(path))]));
const modulePath = resolve(out, 'production-replay.wasm');
const flags = ['--target=wasm32-wasip1', '-DPORT_TITLE=14', '-std=c++17', '-O2',
  '-ffp-contract=off', '-fno-strict-aliasing', '-fno-exceptions', '-fno-rtti',
  '-mexec-model=reactor', '-Wl,--no-entry', '-Wl,--export-memory', '-Wl,-z,stack-size=1048576'];
execFileSync(resolve(root, 'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),
  [...flags, fixture, ...objects, '-o', modulePath],
  {cwd:rt, env:{...process.env, TEMP:out, TMP:out, TMPDIR:out}, windowsHide:true, stdio:'inherit'});
const moduleBytes = readFileSync(modulePath);
const wasi = new WASI({version:'preview1', args:[], env:{}, preopens:{}});
const {instance} = await WebAssembly.instantiate(moduleBytes, {wasi_snapshot_preview1:wasi.wasiImport});
wasi.initialize(instance);
const c = instance.exports;
const upload = bytes => {const pointer = c.allocate(bytes.length); new Uint8Array(c.memory.buffer, pointer, bytes.length).set(bytes); return pointer;};
const text = pointer => {const bytes = new Uint8Array(c.memory.buffer); return new TextDecoder().decode(bytes.subarray(pointer, bytes.indexOf(0, pointer)));};
const target = JSON.parse(readFileSync(resolve(root, 'runtimes/th14/target.json')));
const archive = readFileSync(target.dataArchives['th14.dat'].path);
assert.equal(c.open_archive(upload(archive), archive.length), 1);
c.production_clock_begin();
assert.equal(c.public_replay_begin(upload(replay), replay.length), 1);
const rows = [], active = [], transitions = [];
let frames=0, error='', observations=c.public_replay_observations(), stage=c.public_replay_status(0);
for (let frame=1; frame<=200000; ++frame) {
  c.production_clock_set(BigInt(frame)*1000000000n/60n);
  if (!c.tick(0) || !c.draw()) {error=text(c.error()); break;}
  c.production_capture_retire(); // Explicit headless postDraw: there is no GPU target.
  if (!c.public_replay_clock(frame/60)) {error='Spell clock rejected'; break;}
  frames=frame;
  const nextObservations=c.public_replay_observations(), nextStage=c.public_replay_status(0);
  assert(nextObservations===observations || nextObservations===observations+1, 'Physical callback lost or duplicated');
  if (nextObservations===observations+1) {
    rows.push(...new Uint32Array(c.memory.buffer, c.reference_data(), 32));
    active.push(c.public_replay_observed_active());
  }
  observations=nextObservations;
  if (nextStage!==stage) {transitions.push({frame, from:stage, to:nextStage, phase:c.phase()}); stage=nextStage;}
  if ([3,4,5].includes(c.phase())) break;
}
const selected=Buffer.from(new Uint32Array(rows).buffer), activity=Buffer.from(active);
for (const [name, expected] of Object.entries(build.sourceHashes))
  assert.equal(sha(readFileSync(resolve(rt, name))), expected, `Source changed during run: ${name}`);
for (const [name, expected] of Object.entries(fixtureHashes))
  assert.equal(sha(readFileSync(resolve(rt, 'tests/cpp', name))), expected, `Fixture changed during run: ${name}`);
for(const [name,expected]of Object.entries(fixtureDependencyHashes))
  assert.equal(sha(readFileSync(resolve(root,name))),expected,`Fixture dependency changed during run: ${name}`);
writeFileSync(resolve(out, 'selected-state.u32'), selected);
writeFileSync(resolve(out, 'callback-active.u8'), activity);
const ended=!error && c.phase()===4 && !c.public_replay_status(3);
const report={productionPlaybackVerified:ended, completeGame:false, nativeEquivalent:false,
  frames, phase:c.phase(), stage, error, candidatePlaybackEnded:ended,
  gameOverRequested:!!c.public_replay_status(3), unsupported:c.public_replay_status(6), skipped:c.public_replay_status(5),
  selectedCallbacks:active.length, inactiveCallbacks:active.filter(value=>!value).length, allPhysicalCallbacksRetained:true,
  transitions, forcedProgression:false, invulnerabilityOverride:false,
  clockMode:'Declared test input floor(frame*1e9/60) via the production monotonic-clock callback; not retail scheduler time',
  gpuPrepared:false, captureRetirement:'Explicit no-target consumer after each successful headless draw', sourceHashes:build.sourceHashes, objectHashes,
  engineBuildSha256:sha(buildBytes), fixtureHashes, fixtureDependencyHashes, generatedFixtureSha256:sha(readFileSync(fixture)),
  compileFlags:flags, wasmSha256:sha(moduleBytes), wasmBytes:moduleBytes.length,
  replaySha256:sha(replay), replaySourceSha256:sha(metadataBytes), archiveSha256:sha(archive),
  selectedStateSha256:sha(selected), callbackActiveSha256:sha(activity), toolSha256:sha(readFileSync(import.meta.filename)),
  scope:'Fresh current production core and ordinary intact public replay. Headless resource preparation and explicitly controlled clock; no SDL upload, native scheduling, pixels, audio, browser storage, original natural ending or whole-game equality claim.'};
writeFileSync(resolve(out, 'report.json'), JSON.stringify(report, null, 2)+'\n');
console.log(JSON.stringify({label, frames, phase:report.phase, ended, error, inactiveCallbacks:report.inactiveCallbacks}));
assert(ended && !report.unsupported && !report.skipped, 'Production replay did not complete cleanly');
