// Resource-backed integration only: this is not a native STD or pixel oracle.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th13/stage-check');
mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,[resolve(root,'runtimes/th13/th13_web/scripts/cpp/build-engine.mjs')],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th13'),wasm=resolve(out,'stages.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=13',
 'tests/cpp/th13-stage-fixture.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const sha=b=>createHash('sha256').update(b).digest('hex'),archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th13.json'),'utf8')),hashes={};
const data=(name,fn)=>{const row=archive.decoded.find(r=>r.name===name),b=readFileSync(resolve(archive.extraction,name));assert.equal(sha(b),row.sha256);hashes[name]=row.sha256;const p=c.allocate(b.length);try{new Uint8Array(c.memory.buffer,p,b.length).set(b);return fn(p,b.length);}finally{c.release(p);}};
const error=()=>{const b=new Uint8Array(c.memory.buffer,c.last_error(),512);return new TextDecoder().decode(b.subarray(0,b.indexOf(0)));};
assert.equal(data('text.anm',(p,n)=>c.open_resource(1,p,n)),1);
const stages=[];
for(let stage=1;stage<=7;++stage){
 const anm=`st0${stage}wl.anm`,std=`st0${stage}.std`;
 assert.equal(data(anm,(p,n)=>c.open_resource(0,p,n)),1,anm);
 assert.equal(data(std,(p,n)=>c.start(p,n,stage)),1,`${std}: ${error()}`);
 let submissions=0,primitives=0,ribbons=0;
 for(let frame=0;frame<1200;++frame){assert.equal(c.tick(),1,`stage ${stage} frame ${frame}: ${error()}`);assert.equal(c.count(0),frame+1);submissions+=c.count(1);primitives+=c.count(2);ribbons+=c.count(3);}
 assert.ok(submissions>0&&primitives>0,`stage ${stage} submits geometry`);
 stages.push({stage,frames:1200,submissions,primitives,ribbons});
}
assert.ok(stages[2].ribbons>0,'third stage submits the original effect-5 world strip');
const engine=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th13-build.json'),'utf8'));
const report={passed:true,scope:'Seven retail STD/ANM backgrounds: 1200 production update/draw frames each, without ECL, players, or native STD/pixel comparison.',stages,resourceHashes:hashes,wasmSha256:sha(bytes),sourceHashes:engine.sourceHashes,
 toolHashes:Object.fromEntries(['tools/th13-stage-check.mjs','runtimes/th12/th12_web/tests/cpp/th13-stage-fixture.cpp'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th13-stage-integration.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
