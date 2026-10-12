import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/anm-texture-precision');mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(resolve(root,p));
const nativeBytes=read('artifacts/th14/anm-texture-precision-native.json'),native=JSON.parse(nativeBytes),objects=JSON.parse(read('artifacts/th14/dialogue-text-check/objects.json'));
assert.equal(native.toolSha256,sha(read('tools/th14-anm-texture-precision-native.py')));assert.equal(native.executableSha256,sha(readFileSync('H:/Games/th/14/th14.exe')));
for(const [p,h] of Object.entries(objects.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h,p);for(const [p,h] of Object.entries(objects.objectHashes))assert.equal(sha(readFileSync(p)),h,p);
const fixture='tests/cpp/th14-anm-texture-precision-fixture.cpp',wasm=resolve(out,'precision.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...Object.keys(objects.objectHashes),'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const wasmBytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(wasmBytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const r of native.rows){const p=c.reference(r.seed,r.value,r.control===0x37f?1:0),actual=Array.from(new Uint32Array(c.memory.buffer,p,6));assert.deepEqual(actual,[r.result,r.postControl===0x37f?1:0,...r.rng],JSON.stringify(r));}
const target=JSON.parse(read('runtimes/th14/target.json')),archive=readFileSync(target.dataArchives['th14.dat'].path),p=c.allocate(archive.length);new Uint8Array(c.memory.buffer,p,archive.length).set(archive);assert.equal(c.open_archive(p,archive.length),1); // Archive borrows this buffer until the session is destroyed.
const loading=[];
for(const ticks of [0,904,0xffffffff]){
 assert.equal(c.core_begin(ticks),1);assert.equal(c.core_precision(),0,'cold text/ascii templates and loading root do not FNINIT');
 const timeline=[{frame:0,high:false}];
 for(let frame=1;frame<=10;frame++){assert.equal(c.core_tick(0),1);timeline.push({frame,high:!!c.core_precision()});if(frame<=9)assert.equal(c.core_job(frame-1),1);}
 assert(timeline.some(r=>r.high),'actual loading children reset precision');
 const first=timeline.find(r=>r.high).frame;assert(timeline.filter(r=>r.frame>=first).every(r=>r.high));loading.push({ticks,firstHighFrame:first,timeline});
}
const report={passed:true,completeGame:false,nativeEquivalent:false,referenceCases:native.rows.length,loading,sourceHashes:objects.sourceHashes,nativeProofSha256:sha(nativeBytes),wasmSha256:sha(wasmBytes),fixtureSha256:sha(readFileSync(resolve(rt,fixture))),toolSha256:sha(readFileSync(import.meta.filename)),scope:native.scope+' Three actual-resource cold loading sequences verify initial low precision, natural floating RNG transition and persistence. Scheduling and whole retail upload timeline equality excluded.'};
writeFileSync(resolve(root,'docs/porting/th14-anm-texture-precision-verified-oct12.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({passed:true,referenceCases:report.referenceCases,loading:loading.map(({ticks,firstHighFrame})=>({ticks,firstHighFrame}))}));
