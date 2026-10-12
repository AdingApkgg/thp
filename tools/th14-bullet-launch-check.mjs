import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/bullet-launch-check');mkdirSync(out,{recursive:true});
execFileSync('py',['-3','tools/th14-bullet-launch-native.py'],{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['cpp/game/BulletTh14Launch.cpp','cpp/game/Movement.cpp','tests/cpp/th14-bullet-launch-fixture.cpp'],wasm=resolve(out,'launch.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/bullet-launch-native.json'),'utf8'));
for(const r of proof.cases){const p=c.allocate(13*4);new Float32Array(c.memory.buffer,p,13).set([...r.position,r.angle,r.spread,r.speed,r.slow,r.radius,r.aim,...r.player,r.exclusion]);
 try{assert.equal(c.run(r.mode,r.count,r.layers,r.index,r.layer,r.seed,p),Number(r.accepted),JSON.stringify(r));assert.deepEqual(Array.from({length:9},(_,i)=>c.value(i)>>>0),[...r.result,...r.rng],JSON.stringify(r));}finally{c.release(p);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,cases:proof.cases.length,scope:'TH14 single-bullet launch arithmetic: thirteen aiming modes, unknown-mode default, layers, radius, exclusion, velocity and RNG. Native execution stops before animation allocation; no bullet update or collision equivalence claim.',nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,'cpp/game/Rng.hpp','cpp/game/EnemyTh14Emitter.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-bullet-launch-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${proof.cases.length} native TH14 bullet launches.`);
