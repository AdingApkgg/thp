import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th13/camera-check');
mkdirSync(out,{recursive:true});const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync('py',['-3','tools/th13-stage-native.py'],{cwd:root,env,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th13'),wasm=resolve(out,'cameras.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=13',
 'tests/cpp/th13-camera-fixture.cpp',...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th13/stage-native.json'),'utf8'));
const begin=(code,rate)=>{const b=Buffer.from(code,'hex'),p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);assert.equal(c.begin(p,b.length,rate),1);c.release(p);};
const compare=(expected,label)=>{
 expected.values.forEach((v,i)=>assert.ok(Math.abs(c.value(i)-v)<=Math.max(2e-5,Math.abs(v)*2.4e-7),`${label} component ${i}: ${c.value(i)} != ${v}`));
 expected.integers.forEach((v,i)=>assert.equal(c.integer(i)>>>0,v,`${label} integer ${i}`));
};
for(const row of [...proof.rows,...proof.synthetic]){
 begin(row.code,row.rate);
 for(const [frame,expected] of row.timeline.entries()){assert.equal(c.tick(),1,`${row.name} ${frame}`);compare(expected,`${row.name} rate ${row.rate} frame ${frame}`);}
}
for(const row of proof.effects){begin('0000000000000800',row.rate);c.effect(row.kind,row.frame);assert.equal(c.tick(),1);compare(row.output,`effect ${row.kind} rate ${row.rate} frame ${row.frame}`);}
for(const row of proof.culling)assert.equal(c.visible(...row.position,...row.size,...row.instance),row.visible,`culling ${JSON.stringify(row.position)}`);
for(const row of proof.views){
 const p=c.allocate(160),v=new Float32Array(c.memory.buffer,p,40);v.set(row.input);v.set(row.output.lookAt.flat(),16);v.set(row.output.perspective,28);
 c.view_begin(p);assert.equal(c.view_matches(p+64,p+112),1,`native camera arguments ${JSON.stringify(row)}`);c.release(p);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),engine=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th13-build.json'),'utf8'));
const report={passed:true,scope:'Retail STD camera state at three rates, all effect IDs, up interpolation/cancellation, and identity-camera culling. Animation creation is a sink; D3DX projection is a specified identity boundary; no pixel-equivalence claim.',
 nativeExecutableSha256:proof.executableSha256,retailTimelines:proof.rows.length,retailFrames:proof.rows.reduce((n,r)=>n+r.timeline.length,0),effectStates:proof.effects.length,syntheticFrames:proof.synthetic.reduce((n,r)=>n+r.timeline.length,0),culling:proof.culling.length,cameraArgumentCases:proof.views.length,
 resourceHashes:Object.fromEntries(proof.rows.map(r=>[r.name,r.sha256])),wasmSha256:sha(bytes),sourceHashes:engine.sourceHashes,
 toolHashes:Object.fromEntries(['tools/th13-stage-native.py','tools/th13-camera-check.mjs','runtimes/th12/th12_web/tests/cpp/th13-camera-fixture.cpp'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th13-camera-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.retailFrames} retail STD frames, ${report.effectStates} effect states, ${report.syntheticFrames} synthetic frames, ${report.culling} culling cases.`);
