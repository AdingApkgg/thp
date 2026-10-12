import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-emitter-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-enemy-emitter-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['EnemyTh14Emitter','EnemyTh14Commands','EnemyState','EclContext','Movement','Interpolation'].map(n=>'cpp/game/'+n+'.cpp');sources.push('tests/cpp/th14-enemy-emitter-fixture.cpp');const wasm=resolve(out,'emitters.wasm');
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14','tests/cpp/th14-enemy-emitter-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-emitter-native.json'),'utf8'));
for(const row of proof.cases){
 const input=Buffer.from(row.initial,'hex'),p=c.allocate(input.length),a=c.allocate(64);new Uint8Array(c.memory.buffer,p,input.length).set(input);new Uint32Array(c.memory.buffer,a,16).set(row.args);
 try{assert.equal(c.run(row.op,row.difficulty,p,a),0,`op ${row.op} case ${row.n}`);const output=c.output(),actual=Buffer.from(c.memory.buffer,output,input.length),expected=Buffer.from(row.result,'hex');
 if(!actual.equals(expected)){let at=0;while(actual[at]===expected[at])++at;assert.fail(`op ${row.op} case ${row.n}, first different native byte +0x${(at+0x598).toString(16)}: ${actual[at]} != ${expected[at]}`);}
 }finally{c.release(p);c.release(a);}
}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:true,cases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,
 scope:'TH14 600, 602..612, 614, 624..628, 641 emitter configuration, including the 626 polar base vector, sixteen 0x380-byte descriptors and eighteen 0x2c-byte transform records. Native argument reads and memset are boundaries. Bullet emission, trajectories and transform execution are not covered.',
 wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/EnemyTh14Emitter.hpp','cpp/game/EnemyState.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-enemy-emitter-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} TH14 emitter configuration cases.`);
