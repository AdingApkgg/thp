import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/enemy-bomb-damage-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-enemy-bomb-damage-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th14-enemy-bomb-damage-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'damage.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/enemy-bomb-damage-native.json'),'utf8'));
assert.equal(c.default_ratio(),0x3f800000,'constructor ratio');
assert.equal(c.default_hit_sound(),-1,'constructor hit sound');
for(const r of proof.hits)assert.deepEqual([[c.hit_sound(r.override,r.flags,r.spell,r.health)>>>0,0xc1440000]],r.sound.map(s=>[s[0]>>>0,s[1]]),JSON.stringify(r));
for(const r of proof.cases){
 assert.equal(c.run(r.ratio,r.damage,r.active)>>>0,r.result,JSON.stringify(r));assert.equal(c.ratio_value()>>>0,r.ratio);
 assert.equal(c.sound_requested(),+!!r.sound.length,JSON.stringify(r));if(r.sound.length)assert.deepEqual(r.sound,[[36,0xc1440000]]);
}
const sha=b=>createHash('sha256').update(b).digest('hex'),sources=[fixture,'cpp/game/EnemyTh14Commands.cpp','cpp/game/EnemyCommands.hpp','cpp/game/EnemyState.cpp','cpp/game/EnemyState.hpp','cpp/game/EnemyFrame.cpp','cpp/game/EnemyScript.cpp'];
const report={passed:true,cases:proof.cases.length,hitSoundCases:proof.hits.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'ECL 565 raw f32 ratio setter 427704 and actual 423b27..423b72 damage scaling: only bomb state 1 and ratio less than 1, signed i32-to-f32 rounding, CVTTSS2SI behavior, sound 36 for nonzero damage and nonpositive ratio. Includes ten ratio bit patterns (signed zero, NaN and infinities), nine signed damage values and three bomb states. Port constructor default ratio 1 matches retail 422fd5. Native argument getter and sound queue are controlled. Production ECL dispatch and shared scaling helper execute; ECL 553 hit-sound setter and actual 423f61..42407c consumer across 240 override/flags/spell/health cases also agree, including default sound 34 and low-health sound 35. Full shot accumulation, player damage, frame flash behavior, Bomb mechanics and complete gameplay remain unverified.',sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-enemy-bomb-damage-verified.json'),JSON.stringify(report,null,2)+'\n');console.log(`PASS: ${report.cases} retail bomb damage cases.`);
