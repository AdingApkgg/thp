import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/keys-session-check');mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,[resolve(root,'runtimes/th13/th13_web/scripts/cpp/build-engine.mjs'),'--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-keys-session-fixture.cpp',wasmPath=resolve(out,'keys-session.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasmPath],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasmPath),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
// ArchiveView retains this buffer for the session lifetime.
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const text=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));},config=p=>Buffer.from(new Uint8Array(c.memory.buffer,p,92));let ticks=0;
const tick=(keys=0)=>{assert.equal(c.tick(keys),1,text(c.error()));++ticks;},key=mask=>{tick(mask);tick();};
const wait=(screen,state)=>{for(let i=0;i<240;++i){if(c.menu_value(0)===screen&&c.menu_value(1)===state)return;tick();}assert.fail(`menu did not reach ${screen}/${state}: ${Array.from({length:4},(_,n)=>c.menu_value(n))}`);};
const select=index=>{for(let i=0;i<12&&c.menu_value(2)!==index;++i)key(32);assert.equal(c.menu_value(2),index);};
assert.equal(c.open_title(),1,text(c.error()));c.set_user_config();c.mark_config();wait(1,2);const baseline=config(c.persistent_config_bytes()),rows=[];
for(const route of [{name:'swap-save',row:0,button:1,action:'save'},{name:'pause-save',row:3,button:30,action:'save'},{name:'cancel',row:2,button:7,action:'cancel'},{name:'reset-save',row:1,button:0,action:'reset'},{name:'unassignable-button31',row:0,button:31,action:'save'}]){
 wait(1,2);select(7);key(1);wait(3,2);select(2);key(1);wait(4,2);assert.equal(c.menu_value(3),6);select(route.row);
 const before=config(c.persistent_config_bytes()),expected=Buffer.from(before);c.controller_sample((1<<route.button)>>>0);tick();c.controller_sample(0);tick();assert.deepEqual(config(c.persistent_config_bytes()),before,'editing cannot commit early');
 if(route.action==='save'&&route.button<31){const old=before.readInt16LE(4+route.row*2);for(let i=0;i<4;++i)if(i!==route.row&&before.readInt16LE(4+i*2)===route.button)expected.writeInt16LE(old,4+i*2);expected.writeInt16LE(route.button,4+route.row*2);}
 if(route.action==='reset'){select(4);key(1);assert.equal(c.menu_value(0),4);assert.equal(c.menu_value(1),2);}
 select(5);key(route.action==='cancel'?2:1);wait(3,2);assert.deepEqual(config(c.config_bytes()),expected);assert.deepEqual(config(c.persistent_config_bytes()),expected,'entire92-byte persistent buffer');
 key(2);assert.equal(c.menu_value(2),4);key(2);wait(1,2);assert.deepEqual(config(c.persistent_config_bytes()),expected);
 assert.equal(c.return_title(),1,text(c.error()));wait(1,2);assert.deepEqual(config(c.config_bytes()),expected,'fresh title retains edited user config');
 rows.push({...route,configSha256:createHash('sha256').update(expected).digest('hex'),bindings:Array.from({length:10},(_,n)=>expected.readInt16LE(4+n*2))});
}
assert.equal(c.draw(),1,text(c.error()));const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,completeGame:false,nativeEquivalent:false,cases:rows,ticks,bytesCompared:92,baselineSha256:sha(baseline),archiveSha256:sha(dat),wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([fixture,'tests/cpp/th14-config-session-fixture.cpp','cpp/game/TitleKeys.cpp','cpp/game/TitleOptions.cpp','cpp/game/GameSession.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Actual production GameSession and retail resources, normal input-driven Main→Option→Key Config→Option→Main→fresh title routes. Only platform controller mask sample controlled. Full92 bytes compared before commit, after save/cancel/reset, and title reconstruction, including duplicate swap/Pause and untouched opaque bytes. No physical controller, browser IndexedDB or native whole-session equivalence claim.'};writeFileSync(resolve(root,'docs/porting/th14-keys-session-verified-oct11.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,cases:rows.length,ticks,bytesCompared:92}));
