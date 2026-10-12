import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/damage-source-update-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-damage-source-update-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-damage-source-update-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'sources.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/damage-source-update-native.json'),'utf8'));let maxError=0;
const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
for(const [index,r] of proof.rows.entries()){
 assert.equal(c.begin(r.seed),1,`seed${r.seed}`);
 for(const [id,words] of Object.entries(r.areas))for(let k=0;k<37;k++){const value=c.area(+id,k)>>>0,why=JSON.stringify({index,seed:r.seed,id,k});if(k===20||k===21){const error=Math.abs(f(value)-f(words[k]));maxError=Math.max(maxError,error);assert.ok(error<=.00002,why+` error${error}`);}else assert.equal(value,words[k],why);}
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-damage-source-update-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),maxError,scope:'Entire256-record442a20..442b47 loop within player update, native402ff0/403110 and angle math execute with no interception. Seeded active records1/2/256, inactive/rectangle/circle/Bomb flags, linear movement, preserved z velocity, hundredth floor, radius growth/angular velocity, stamp reset, selector clamp, rates0/.5/1/1.5/null fallback at global1, fractional countdown and active expiry.37 words exact except2e-5 x87 velocity tolerance. Other movement modes and whole containing player update/Bomb lifecycle/full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotTh16.cpp','cpp/game/ShotTh16.hpp','cpp/game/PlayerFrame.cpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-damage-source-update-native.py','tools/th16-damage-source-update-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 damage source updates.`);
