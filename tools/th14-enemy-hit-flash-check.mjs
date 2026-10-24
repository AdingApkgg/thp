import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,readdirSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/enemy-hit-flash-check'),rt=resolve(root,'runtimes/th12/th12_web');mkdirSync(out,{recursive:true});
nativePython('tools/th14-enemy-hit-flash-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
let wasm=process.argv[2]&&resolve(process.argv[2]);
if(!wasm){
 const env={...process.env,TEMP:out,TMP:out};
 execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
 const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');wasm=resolve(out,'unit.wasm');
 execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14','tests/cpp/th14-enemy-hit-flash-fixture.cpp',...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
}
const bytes=read(wasm),proof=JSON.parse(read(resolve(out,'native.json'))),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
for(const row of proof.rows){c.run(...row.slice(0,6));assert.deepEqual(Array.from({length:4},(_,i)=>c.value(i)>>>0),row.slice(6),'retail flash '+JSON.stringify(row));}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=['cpp/game/EnemyTh14Commands.cpp','cpp/game/EnemyFrame.cpp','cpp/game/EnemyCommands.hpp','tests/cpp/th14-enemy-hit-flash-fixture.cpp'];
const report={passed:true,cases:proof.rows.length,originalExecutableSha256:proof.originalExecutableSha256,actualBranch:proof.actualBranch,wasmSha256:sha(bytes),controlledEnemyAndVm:true,soundSinkPatched:true,scope:'TH14 retail flash branch 423ee5..42407c: damage-flash countdown, signed phase-clock modulo (native enemy+2c0), native 0x80000000/0x40800000/0x200000 enemy masks, native VM color-mode bits, secondary color and optional hit sound. Twelve flag combinations include former wrong masks; negative/zero/positive countdown and phase clock, with lifetime deliberately different, four spell states, five health boundaries and four dirty VM flag values. Production helper runs through EnemyFrame. Complete gameplay, GPU pixels and audio PCM are outside this unit control.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(read(resolve(rt,p)))]))};
write(resolve(root,'docs/porting/th14-enemy-hit-flash-verified-oct24.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS '+report.cases+' original TH14 hit-flash cases.');
