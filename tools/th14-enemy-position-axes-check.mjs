import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-position-axes-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-enemy-position-axes-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out},wasm=resolve(out,'axes.wasm');
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14','tests/cpp/th14-enemy-position-axes-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-position-axes-native.json'),'utf8'));
const put=values=>{const p=c.allocate(Math.max(7,values.length)*4);new Uint32Array(c.memory.buffer,p,Math.max(7,values.length)).fill(0);new Uint32Array(c.memory.buffer,p,values.length).set(values);return p;};
const actual=()=>({result:Array.from({length:53},(_,i)=>c.value(i)>>>0),position:Array.from({length:2},(_,i)=>Array.from({length:19},(_,n)=>c.position_value(i,n)>>>0)),axis:Array.from({length:2},(_,i)=>Array.from({length:4},(_,n)=>c.axis_value(i,n)>>>0))});
for(const row of proof.rows){const p=put(row.initial.result),a=put(row.args),label=`position axes ${row.op} mode ${row.mode} variant ${row.variant}`;try{
 c.initialize(p,row.rate);for(let i=0;i<2;i++){const v=put(row.initial.position[i]),m=put(row.initial.axis[i]);try{c.position_initialize(i,v,m);}finally{c.release(v);c.release(m);}}assert.equal(c.command(row.op,a),0,label);assert.deepEqual(actual(),row.configured,label+' configured');
 for(const [frame,expected] of row.frames.entries()){assert.equal(c.tick()>>>0,expected.status,label+` frame ${frame} status`);const {status,...state}=expected;assert.deepEqual(actual(),state,label+` frame ${frame}`);}
}finally{c.release(p);c.release(a);}}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=['cpp/game/EnemyTh14Commands.cpp','cpp/game/EnemyState.cpp','cpp/game/EnemyState.hpp','cpp/game/Interpolation.cpp','cpp/game/Interpolation.hpp','cpp/game/Movement.cpp','tests/cpp/th14-enemy-position-axes-fixture.cpp','tests/cpp/th14-enemy-movement-fixture.cpp'];
const report={passed:true,timelines:proof.rows.length,frames:proof.rows.reduce((n,r)=>n+r.frames.length,0),nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-enemy-position-axes-native.py','tools/th14-enemy-position-axes-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))])),scope:'Actual retail 425eb6/426076/4261c6 ECL 434..439, 401/403 and 425/426/427 setup and complete 4230d0 movement/42cd40 position consumption. Single-mode mirrored offsets and independent XYZ modes including persisted common completion mode and third-axis mode; all 32 modes plus -1/80, zero/negative/7/35 durations, sentinels after offset arithmetic, retained clocks/flags, camera/clamp and three rates. Both bands seeded and compared, including clearing independent-axis flags when normal or Hermite setters replace the mode. Zero BSS tangent defaults. Argument getters and ANM lookup controlled; GPU and full campaign excluded.'};
writeFileSync(resolve(root,'docs/porting/th14-enemy-position-axes-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.timelines} position axis timelines / ${report.frames} frames`);
