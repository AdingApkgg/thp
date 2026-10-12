import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/startup-session');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),path=resolve(out,'startup.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','tests/cpp/th14-startup-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1);assert.equal(c.open_title(),1);
const rng=()=>({seed:c.replay_observation(13),calls:c.replay_observation(14)>>>0});
const scripts={};for(const file of [0,1,2])for(const index of file===2?[15,16,17,18]:[0,86,91]){const p=c.startup_script(file,index),size=c.startup_script_size(file,index);if(p)scripts[`${file}:${index}`]=Buffer.from(new Uint8Array(c.memory.buffer,p,size)).toString('hex');}
let previous=rng();const changes=[{frame:0,phase:c.phase(),...previous}];let frame=0;
const titleStates=[];
while(c.phase()===0&&frame<5000){++frame;assert.equal(c.tick(0),1);assert.equal(c.draw(),1);if(frame<3||frame%180===0)titleStates.push({frame,state:Array.from({length:4},(_,n)=>c.startup_state(n))});const state=rng();if(state.calls!==previous.calls){changes.push({frame,phase:c.phase(),...state});previous=state;}}
assert.equal(c.phase(),1,'natural first automatic attract enters stage');assert.equal(c.tick(0),1);assert.equal(c.draw(),1);changes.push({frame:frame+1,phase:c.phase(),...rng()});
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/native-startup-visual-rng-threads-oct10.json'),'utf8')),report={passed:true,nativeEquivalent:false,titleFrames:frame,changes,nativeCapturedInitialClockSeed:native.rngWrites[0].rng[0],nativeFirstStageRng:native.frames[0].scriptRng,productionClockSeed:0,productionFirstStageRng:rng(),sha256:createHash('sha256').update(bytes).digest('hex'),scope:'Production natural first title and no-input automatic attract using original resources, with actual animation updates/draw calls. Records all visual RNG count changes. Clock inputs differ from retail capture; no seed or final count forced, and count observations alone are not animation/GPU equivalence.'};
report.titleStates=titleStates;report.scripts=scripts;report.creations=Array.from({length:c.startup_creation_count()},(_,n)=>Array.from({length:6},(_,k)=>c.startup_creation_value(n,k)));
writeFileSync(resolve(root,'docs/porting/th14-startup-session-observed-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({titleFrames:frame,changes:changes.length,firstStage:rng(),nativeFirstStage:native.frames[0].scriptRng,nativeEquivalent:false}));
