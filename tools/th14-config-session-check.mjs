import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/config-session-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-config-session-fixture.cpp',path=resolve(out,'config-session.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
const config=p=>Buffer.from(new Uint8Array(c.memory.buffer,p,92));
const error=()=>{const b=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
assert.equal(c.open_title(),1,error());const expected=config(c.set_user_config()),rows=[];
for(let demo=0;demo<3;++demo){
 assert.equal(c.begin_demo(demo),1,error());assert.equal(c.phase(),1);
 assert.notDeepEqual(config(c.config_bytes()),expected,'recorded configuration still governs playback');
 for(let f=0;f<120;++f){assert.equal(c.tick(0),1,error());assert.equal(c.draw(),1,error());assert.deepEqual(config(c.persistent_config_bytes()),expected,'saving during replay retains user configuration');}
 assert.equal(c.return_title(),1,error());assert.deepEqual(config(c.config_bytes()),expected,'return to title restores every configuration byte');
 rows.push({demo,frames:120,passed:true});
 for(const key of [256,1,2]){
  assert.equal(c.begin_demo(demo),1,error());
  for(let f=0;f<8;++f)assert.equal(c.tick(key),1,error());
  assert.equal(c.tick(0),1,error());assert.equal(c.phase(),0);
  assert.equal(c.title_screen(),1,'held demo-cancel key cannot also activate/cancel the fresh main menu');
  assert.deepEqual(config(c.config_bytes()),expected);
 }
}
for(let f=0;f<1801;++f)assert.equal(c.tick(0),1,error());assert.equal(c.phase(),1,'automatic attract demo starts');assert.deepEqual(config(c.persistent_config_bytes()),expected);
assert.equal(c.return_title(),1,error());assert.deepEqual(config(c.config_bytes()),expected);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-config-session-verified.json'),JSON.stringify({passed:true,cases:rows,automaticAttract:true,heldCancelCases:9,bytesPreserved:92,archiveSha256:sha(dat),wasmSha256:sha(bytes),scope:'Production GameSession replay/attract configuration isolation with all three original demos and real resources; all92 user bytes preserved during replay saves and restored on return to title. Original recorded config remains active during playback. Nine eight-frame held Return/Shoot/Bomb cancellation paths remain at Main without a second menu action. This is integration regression, not native config lifecycle or IndexedDB/browser proof.',sourceHashes:Object.fromEntries([fixture,'cpp/game/GameSession.cpp','cpp/game/GameSession.hpp','cpp/sdl/Application.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log('PASS three retail demo config isolation/return paths and automatic attract; all92 user bytes preserved');
