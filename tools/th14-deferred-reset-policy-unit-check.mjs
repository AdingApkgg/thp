// Isolated v3 source clone plus the one requested full-session reset policy.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync,cpSync} from 'node:fs';
import {resolve,relative,dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),home=resolve(root,'artifacts/th14/deferred-reset-policy-unit-oct14');
const v3=resolve(root,'artifacts/th14/staged-loader-integration-oct14/cancel-v3'),frozenBytes=readFileSync(resolve(v3,'frozen-source.json')),frozen=JSON.parse(frozenBytes);
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const originalRoot=resolve(frozen.sourceRoot),sourceRoot=resolve(home,'source/runtimes'),rt=resolve(sourceRoot,'th12/th12_web');
const bind=path=>{const bytes=readFileSync(path);return {path:relative(root,path).replaceAll('\\','/'),bytes:bytes.length,sha256:sha(bytes)};};
for(const row of frozen.files){const b=readFileSync(resolve(originalRoot,row.path));assert.equal(b.length,row.bytes);assert.equal(sha(b),row.sha256,row.path);}
const reuse=process.argv.includes('--reuse-compiled');
if(!reuse){assert(!existsSync(sourceRoot),'Choose a new source clone for a new result');mkdirSync(dirname(sourceRoot),{recursive:true});cpSync(originalRoot,sourceRoot,{recursive:true});}
const policy=resolve(rt,'cpp/game/GameSession.cpp'),before=readFileSync(resolve(originalRoot,'th12/th12_web/cpp/game/GameSession.cpp')).toString();
const old='bool clear_animations(AnmManager& manager) {\r\n    manager.clear();';
const oldLf='bool clear_animations(AnmManager& manager) {\n    manager.clear();';
const needle=before.includes(old)?old:oldLf,newline=needle===old?'\r\n':'\n';assert.equal(before.split(needle).length,2);
const expectedPolicy=before.replace(needle,['bool clear_animations(AnmManager& manager) {','#if PORT_TITLE == 14','    manager.retire_deferred_captures_without_target();','#endif','    manager.clear();'].join(newline));
if(!reuse)writeFileSync(policy,expectedPolicy);else assert.equal(readFileSync(policy).toString(),expectedPolicy);
const sourceChanges=[];for(const row of frozen.files){const p=resolve(sourceRoot,row.path);if(sha(readFileSync(p))!==row.sha256)sourceChanges.push(row.path);}assert.deepEqual(sourceChanges,['th12/th12_web/cpp/game/GameSession.cpp']);
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),objects=resolve(home,'objects');mkdirSync(objects,{recursive:true});
const flags=['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti'];
const compile=args=>new Promise((accept,reject)=>{const p=spawn(compiler,args,{cwd:rt,windowsHide:true,env:{...process.env,TEMP:objects,TMP:objects,TMPDIR:objects},stdio:['ignore','pipe','pipe']});let log='';p.stdout.on('data',b=>log+=b);p.stderr.on('data',b=>log+=b);p.on('error',reject);p.on('exit',code=>code?reject(Error(log)):accept());});
const engine=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json'))),paths=new Array(engine.sources.length);let cursor=0;
const fixture=resolve(home,'fixture.cpp'),wasm=resolve(home,'reset-policy-unit.wasm');
if(!reuse){
 await Promise.all(Array.from({length:3},async()=>{while(cursor<engine.sources.length){const i=cursor++,name=engine.sources[i],out=resolve(objects,name.replaceAll('/','_')+'.o');await compile([...flags,'-c',name,'-o',out]);paths[i]=out;}}));
 await compile([...flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...paths,'-o',wasm]);
}else{
 const build=JSON.parse(readFileSync(resolve(home,'prepared-build.json')));
 for(const [name,h] of Object.entries(build.sourceHashes))assert.equal(sha(readFileSync(resolve(sourceRoot,name))),h);
 assert.equal(sha(readFileSync(fixture)),build.fixtureSha256);assert.equal(sha(readFileSync(wasm)),build.wasmSha256);
 for(let i=0;i<engine.sources.length;++i){const p=resolve(objects,engine.sources[i].replaceAll('/','_')+'.o');assert.equal(sha(readFileSync(p)),build.objects[p.split(/[\\/]/).at(-1)]);paths[i]=p;}
}
const moduleBytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(moduleBytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path),archivePointer=c.allocate(archive.length);new Uint8Array(c.memory.buffer,archivePointer,archive.length).set(archive);assert.equal(c.open_archive(archivePointer,archive.length),1);
const cases=[];for(let which=0;which<4;++which){const pointer=c.reset_policy_case(which),words=Array.from(new Uint32Array(c.memory.buffer,pointer,12));
 assert.equal(words[0],1);assert.equal(words[1],1);assert.equal(words[2],0);assert.equal(words[3],1);assert.equal(words[4],1);
 if(which<3){assert.equal(words[5],0xffffffff);assert.equal(words[6],0);if(which>0)assert.equal(words[7],0);}else{assert.equal(words[5],words[2]);assert.equal(words[6],1);}
 cases.push({operation:['direct unrecorded stage3','new begin stage1','open_title','ordinary manager.clear'][which],words,queueCancelled:which<3,ordinaryManagerClearRetainsQueue:which===3});}
const bindings=[bind(import.meta.filename),bind(fixture),bind(policy),bind(wasm),bind(compiler),bind(resolve(v3,'frozen-source.json')),bind(resolve(rt,'cpp/game/PauseEnd.cpp')),bind(resolve(rt,'cpp/game/AnmManager.cpp')),bind(resolve(rt,'cpp/game/AnmManager.hpp')),bind(resolve(rt,'cpp/game/DeferredCaptureQueueTh14.hpp'))];
if(reuse)bindings.push(bind(resolve(home,'prepared-build.json')),bind(resolve(home,'failed-first-run.json')),bind(resolve(home,'failed-first-run-tool.mjs')));
const report={privateResetPolicyVerified:true,productionChanged:false,productionVerified:false,nativeEquivalent:false,completeGame:false,cases,originalV3SourceManifestSha256:sha(frozenBytes),sourceChanges,sourceBindings:bindings,objects:paths.map(bind),compilerFlags:flags,archiveSha256:sha(archive),actualGraphicsCopyExecuted:false,scope:'Four independent real-DAT GameSession/PauseEnd units. Declared begin_end(false,true) constructs actual text52 and enqueues one actual deferred file0 copy; no postDraw occurs before direct stage3, fresh begin stage1 or open_title. The isolated one-hunk full-session/direct-stage clear_animations policy cancels those records; unchanged ordinary AnmManager.clear still preserves them. No actual game clear, Native pooled-VM destruction cancellation, graphics copy, screenshot/pixels, full loader or production execution claim.'};
const output=resolve(root,'docs/porting/th14-deferred-reset-policy-unit-verified-oct14.json');assert(!existsSync(output));writeFileSync(output,JSON.stringify(report,null,2)+'\n');
for(const row of frozen.files)assert.equal(sha(readFileSync(resolve(originalRoot,row.path))),row.sha256,'Original v3 snapshot changed');
console.log(JSON.stringify({privateResetPolicyVerified:true,cases:cases.length,objects:paths.length,sourceChanges,moduleSha256:sha(moduleBytes),reportSha256:sha(readFileSync(output))}));
