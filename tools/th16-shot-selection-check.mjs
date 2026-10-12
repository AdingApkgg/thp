import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve('.'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/shot-selection-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};nativePython('tools/th16-shot-selection-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const fixture='tests/cpp/th16-shot-selection-fixture.cpp',dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'options.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/shot-selection-native.json'),'utf8'));
let previous='';const mains=['pl00','pl02','pl03','pl01'],seasons=['pl00sub','pl02sub','pl03sub','pl01sub','pl04sub'];
for(const [index,r] of proof.rows.entries()){
 const key=`${r.character}/${r.season}`;if(key!==previous){for(const [sub,name] of [[0,mains[r.character]],[1,seasons[r.season]]]){const data=readFileSync(resolve(root,'artifacts/th16/options-corpus',`${name}.sht`)),p=c.allocate(data.length);new Uint8Array(c.memory.buffer,p,data.length).set(data);assert.equal(c.open(p,data.length,sub),1,name);}previous=key;}
 const why=JSON.stringify({index,character:r.character,season:r.season,power:r.power,points:r.points,focus:r.focus,frame:r.frame,longFrame:r.longFrame});assert.equal(c.begin(r.power,r.points,r.focus,r.frame,r.longFrame),1,why);
 assert.deepEqual(Array.from({length:c.count()},(_,n)=>[c.event(n,0)>>>0,c.event(n,1)>>>0]),r.events,why);
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-shot-selection-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.rows.length,nativeExecutableSha256:proof.executableSha256,resources:proof.resources,wasmSha256:sha(bytes),scope:'Complete445470 with nine actual SHTs, both families, power/focus and season groups, regular and long clock period/delay, packed group/spec/family and ordered spawn requests.445360 allocation is a controlled boundary. Production shot spawn/update/collision, scheduler clocks, resources and full gameplay excluded.',sourceHashes:Object.fromEntries([fixture,'cpp/game/ShotSchedule.cpp','cpp/game/ShotSchedule.hpp','cpp/game/SeasonTh16.cpp','cpp/game/SeasonTh16.hpp','cpp/game/ShtResource.cpp','cpp/game/ShtResource.hpp'].map(s=>[s,sha(readFileSync(resolve(rt,s)))])),toolHashes:Object.fromEntries(['tools/th16-shot-selection-native.py','tools/th16-shot-selection-check.mjs'].map(s=>[s,sha(readFileSync(resolve(root,s)))]))},null,2)+'\n');
console.log(`PASS: ${proof.rows.length} native TH16 main/season shot selections on nine retail SHTs.`);
