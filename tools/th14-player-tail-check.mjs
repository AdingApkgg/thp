import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/player-tail-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th14-player-tail-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-player-tail-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'tail.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/player-tail-native.json'),'utf8'));
const dat=readFileSync(JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')).dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const compare=(r,label)=>assert.deepEqual(Array.from({length:c.size()},(_,i)=>c.value(i)>>>0),r.result,label);
for(const r of proof.parameters)for(const subtype of [0,1]){assert.equal(c.parameters(r.character*2+subtype),1);compare(r,`parameters ${r.character}/${subtype}`);}
for(const r of proof.stages){assert.equal(c.stage(...r.args),1);compare(r,`stage ${r.args}`);assert.deepEqual([[c.lives()>>>0,c.fragments()>>>0]],r.events);}
for(const r of proof.tails)for(const warp of [0,99]){assert.equal(c.tail(...r.args,warp),1);compare(r,`tail ${r.args} warp ${warp}`);assert.equal(!!c.fire(),r.fire);}
for(const r of proof.blinks){assert.equal(c.blink(...r.args),1);compare(r,`blink ${r.args}`);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-player-tail-verified.json'),JSON.stringify({passed:true,completeGame:false,parameterCases:6,stageCases:proof.stages.length,tailCases:proof.tails.length,tailPortCases:proof.tails.length*2,blinkCases:proof.blinks.length,nativeExecutableSha256:proof.executableSha256,archiveSha256:sha(dat),wasmSha256:sha(bytes),scope:'Own44c681..44c9dc table copies/initial bounds compared to all six production PlayerFrame initializers using original SHT/ANM resources. Complete44cc10 stage reset compares clocks, all33 movement-history entries, full-width life-fragment delivery, scale and known shot caches; ANM lookup, HUD and option factory controlled, pool links/option recreation/focus family retirement excluded. Own44e8d5..44ebda executes all three clocks and complete450fb0 firing cycle, with shot factory/update and ANM lookup boundaries; compares production clock/gate helper and actual ShotManager.fire including no TH11 warp restriction. Own44e0fa..44e1ac blink uses the same production color-mode helper; ANM VM execution excluded. Synthetic empty SHT groups in tail checks. Rank storage observed unchanged natively, whole-session rank scheduling not proven. No native campaign/GPU/pixel equivalence.',sourceHashes:Object.fromEntries([fixture,'cpp/game/PlayerFrame.cpp','cpp/game/PlayerFrame.hpp','cpp/game/ShotSchedule.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th14-player-tail-native.py','tools/th14-player-tail-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS:6 original-resource parameter sets; ${proof.stages.length} stage resets; ${proof.tails.length*2} clock/fire cases; ${proof.blinks.length} blinks`);
