import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/replay-writer-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-replay-writer-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'replay-writer.wasm'),fixture='tests/cpp/th14-replay-writer-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/replay-writer-native.json'),'utf8'));
const upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;};
const view=(p,n)=>Buffer.from(new Uint8Array(c.memory.buffer,p,n));
for(const r of proof.configs){const p=upload(Buffer.from(r.controller,'hex'));assert.equal(view(c.config_default(p),0x5c).toString('hex'),r.config);c.release(p);}
for(const [caseIndex,r] of proof.cases.entries()){
 const cfg=upload(Buffer.from(r.config,'hex'));assert.equal(c.writer_begin(r.selection>>1,r.selection&1,r.difficulty,r.practice,r.timestampLow,r.timestampHigh,cfg),1);c.release(cfg);
 for(const s of r.stages){const h=upload(Buffer.from(s.header,'hex'));assert.equal(c.writer_stage(s.number,h,s.initial),1);c.release(h);const input=Buffer.from(s.inputs,'hex'),fps=Buffer.from(s.fps,'hex');
  for(let n=0;n<s.liveFrames;n++)assert.equal(c.writer_tick(input.readUInt16LE(n*6),input.readUInt16LE(n*6+2),input.readUInt16LE(n*6+4),fps[Math.floor(n/30)]),1);
  assert.equal(c.writer_finish(s.terminal),1);
 }
 const name=upload(Buffer.from(r.name+'\0'));assert.equal(c.writer_save(name,r.score,r.reached,r.continues,r.slowdown),1,`reader rejects case ${caseIndex}`);c.release(name);
 const decoded=view(c.writer_decoded(),c.writer_decoded_size()),native=Buffer.from(r.decoded,'hex');
 assert.deepEqual(decoded,native,`native serialized case ${caseIndex}`);
 writeFileSync(resolve(out,`case-${caseIndex}.rpy`),view(c.writer_data(),c.writer_size()));
}
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=upload(dat);assert.equal(c.open_archive(p,dat.length),1);
const err=()=>{const b=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
for(const r of proof.starts){assert.equal(c.begin(r.stage,0,0,r.difficulty),1,err());assert.deepEqual(Array.from({length:4},(_,n)=>c.session_start_word(n)>>>0),r.values);}
const roundTrips=[];
for(let selection=0;selection<6;selection++){
 assert.equal(c.begin(1,selection>>1,selection&1,1),1,err());const live=[];
 for(let frame=0;frame<600;frame++){const held=1|(frame%120<60?64:128)|(frame%90<45?8:0);assert.equal(c.tick(held),1,err());assert.equal(c.draw(),1,err());live.push(Array.from({length:20},(_,n)=>c.session_word(n)));}
 assert.equal(c.session_save(),1,err());writeFileSync(resolve(out,`session-${selection}.rpy`),view(c.writer_data(),c.writer_size()));assert.equal(c.written_play(),1,err());
 let firstDifference=null;
 for(let frame=0;frame<600;frame++){assert.equal(c.tick(0),1,err());assert.equal(c.draw(),1,err());const replay=Array.from({length:20},(_,n)=>c.session_word(n));if(!firstDifference&&replay.some((v,n)=>v!==live[frame][n]))firstDifference={frame:frame+1,live:live[frame],replay};}
 roundTrips.push({selection,frames:600,firstDifference});console.log(JSON.stringify(roundTrips.at(-1)));
}
const sha=b=>createHash('sha256').update(b).digest('hex'),passed=roundTrips.every(r=>!r.firstDifference);
writeFileSync(resolve(root,'docs/porting/th14-replay-writer-verified.json'),JSON.stringify({passed,nativeSerializedBodies:proof.cases.length,nativeConfigs:proof.configs.length,nativeStarts:proof.starts.length,roundTrips,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'TH14 own4376e0 config initializer with controlled memset; own435caa/435da5 point and power initialization. Own replay header/stage instruction ranges and455490 through entry of4654d0 serialize102 bodies including900-tick chunk boundaries and six three-stage streams; CRT allocation/memory/sprintf are explicit boundaries, timestamps/FPS globals controlled, native compression/filesystem excluded. Portable actual recorder saved files reopen with Replay; decoded bytes compare exactly. Six actual retail GameSession recordings/save/replay exercise ordinary collision, shots and render submissions for600 frames each; first state divergence is reported, no native whole-session or GPU equivalence.',sourceHashes:Object.fromEntries(['cpp/game/Replay.cpp','cpp/game/Replay.hpp','cpp/game/ReplayRecorder.cpp','cpp/game/GameSession.cpp','cpp/game/GameEconomy.hpp','cpp/game/GameConfig.cpp','cpp/game/GameConfig.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log(`${proof.cases.length} native bodies / ${proof.configs.length} configs / ${proof.starts.length} starts; ${roundTrips.filter(r=>!r.firstDifference).length}/6 full state round trips`);if(!passed)process.exitCode=1;
