// Production stored Replay from independent public input. Completion alone is
// candidate evidence; original-process comparisons remain separate.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const replayPath=resolve(root,process.argv[2]),label=process.argv[3];assert(/^[a-z0-9-]{1,64}$/.test(label));
const out=resolve(root,'artifacts/th14/public-replay-playback',label);mkdirSync(out,{recursive:true});
const replay=readFileSync(replayPath),metadata=JSON.parse(readFileSync(replayPath.replace(/\.rpy$/,'-source.json')));assert.equal(sha(replay),metadata.sha256);
const build=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')));
for(const [name,digest] of Object.entries(build.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),digest,name);
const fixture='tests/cpp/th14-public-replay-physical-fixture.cpp',objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'public-replay.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(name=>name.endsWith('.o')).map(name=>resolve(objects,name)),'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;};
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);
assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.public_replay_begin(upload(replay),replay.length),1);
const text=pointer=>{const bytes=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(bytes.subarray(pointer,bytes.indexOf(0,pointer)));};
const rows=[],callbackActive=[],transitions=[],samples=[];let frames=0,error='',previousStage=c.public_replay_status(0),previousObservations=c.public_replay_observations();
for(let frame=1;frame<=200000;frame++){
 if(!c.tick(0)){error=text(c.error());break;}if(!c.draw()){error=text(c.error());break;}
 if(!c.public_replay_clock(frame/60)){error='Production spell clock failed';break;}frames=frame;
 const stage=c.public_replay_status(0),battle=c.public_replay_status(2),observations=c.public_replay_observations();
 assert(observations===previousObservations||observations===previousObservations+1,'No physical callback may be missed or reused');
 if(observations===previousObservations+1){rows.push(...Array.from(new Uint32Array(c.memory.buffer,c.reference_data(),32)));callbackActive.push(c.public_replay_observed_active());}
 previousObservations=observations;
 if(stage!==previousStage){const transition={frame,from:previousStage,to:stage,phase:c.phase(),lives:c.replay_observation(10),score:c.replay_observation(15)};transitions.push(transition);console.log('Stored Replay transition',JSON.stringify(transition));previousStage=stage;}
 if(frame%600===0)samples.push({frame,stage,battleFrame:battle,phase:c.phase(),lives:c.replay_observation(10),power:c.replay_observation(11),bombs:c.replay_observation(12)});
 if(c.phase()===3||c.phase()===4||c.phase()===5)break;
}
const states=Buffer.from(new Uint32Array(rows).buffer),activeBytes=Buffer.from(callbackActive);writeFileSync(resolve(out,'selected-state.u32'),states);writeFileSync(resolve(out,'callback-active.u8'),activeBytes);
const result={diagnosticOnly:true,physicalInvocationOrder:true,transitionCallbacksRetained:true,completeGame:false,nativeEquivalent:false,productionChanged:false,invulnerabilityOverride:false,forcedProgression:false,
 frames,phase:c.phase(),stage:c.public_replay_status(0),gameOverRequested:!!c.public_replay_status(3),error,transitions,samples,
 candidatePlaybackEnded:!error&&c.phase()===4&&!c.public_replay_status(3),selectedSamples:rows.length/32,selectedStateSha256:sha(states),callbackActiveSha256:sha(activeBytes),inactiveCallbacksRetained:callbackActive.filter(v=>!v).length,
 unsupported:c.public_replay_status(6),skipped:c.public_replay_status(5),replaySource:metadata,replaySha256:sha(replay),wasmSha256:sha(bytes),
 sourceHashes:build.sourceHashes,fixtureSha256:sha(readFileSync(resolve(rt,fixture))),includedFixtureSha256:sha(readFileSync(resolve(rt,'tests/cpp/th14-custom-replay-reference-fixture.cpp'))),
 sessionFixtureSha256:sha(readFileSync(resolve(rt,'tests/cpp/th14-session-reference-fixture.cpp'))),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Every fresh before-Player callback, including last-stage transition and repeated scaled clock rows, is retained once. Current production stored Replay with the intact independent public player input and ordinary collision/stock. No external keys, cheats or forced stage/termination. Candidate completion is not real-process equality or natural retail clear; native startup, full six-stage baseline, all-owner memory, physical graphics/audio/storage remain separate.'};
writeFileSync(resolve(out,'report.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({frames,phase:result.phase,stage:result.stage,error,gameOver:result.gameOverRequested,candidatePlaybackEnded:result.candidatePlaybackEnded}));
if(error||!result.candidatePlaybackEnded)process.exitCode=1;
