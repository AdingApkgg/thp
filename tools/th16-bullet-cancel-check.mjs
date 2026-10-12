import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/bullet-cancel-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-bullet-cancel-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'bullet-cancel.wasm'),fixture='tests/cpp/th16-bullet-cancel-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/bullet-cancel-native.json'),'utf8'));
for(const r of proof.cases){assert.equal(c.run_case(r.state,r.flags,r.rate,...r.position,r.effect,r.rewards),1);assert.deepEqual(Array.from({length:10},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify(r));assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>c.event(n)>>>0),r.events.flat(),JSON.stringify(r));}
for(const r of proof.circles)assert.equal(c.circle(r.state,r.delay,r.delayed,r.hitbox,r.radius,r.x,r.y),+r.match,JSON.stringify(r));
const f=b=>{const a=new Uint32Array([b]);return new Float32Array(a.buffer)[0];};
for(const r of proof.circles.filter(r=>!r.delayed))for(const op of [615,616]){
 assert.equal(c.route_circle(r.state,r.delay,r.hitbox,r.radius,r.x,r.y,op),0,JSON.stringify(r));assert.equal(c.route_state_value(),r.match?4:r.state,JSON.stringify(r));
 const x=f(r.x),y=f(r.y),inside=!(-192>=x+32||x-32>=192||0>=y+32||y-32>=448);assert.equal(c.route_reward_count(),+(op===615&&r.match&&inside),JSON.stringify({op,...r}));
}
assert.equal(c.route_empty(613),0);assert.equal(c.route_empty(615),0);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-bullet-cancel-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,cases:proof.cases.length,circleCases:proof.circles.length,nativeExecutableSha256:proof.executableSha256,scope:'Complete retail416840 primary cancellation with rewards0/1/3, original416a00 counter executes, controlled VM update/effect factory/sound. Compare state4, SSE half displacement, lifetime reset and ordered requests. Native effect-ID cache stores observed but not yet mapped; secondary VMs, actual factories and full gameplay excluded. Complete416c20/416d20 walkers with cancel sink verify state gates, delayed filtering, ordered COMISS radius inclusion, NaN and infinity.',wasmSha256:sha(bytes),sourceHashes:Object.fromEntries(['cpp/game/BulletTh16.cpp','cpp/game/BulletTh16.hpp','cpp/game/BulletManager.cpp','cpp/game/BulletManager.hpp','cpp/game/BulletState.hpp','cpp/game/Timer.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
const reportPath=resolve(root,'docs/porting/th16-bullet-cancel-verified.json'),report=JSON.parse(readFileSync(reportPath,'utf8'));
report.eclRequestsObserved=proof.requests.length;report.ecl616RoutedCases=proof.circles.filter(r=>!r.delayed).length;report.scope+=' Own ECL613/616 native requests observed with empty original laser list. Production615/616 runs through actual EnemyScriptServices and BulletManager over2304 circle cases using real synthetic ANM binding. Nonempty TH16 lasers are rejected; ECL615 and616 both routed; in-bounds reward1/3 increments own counter without item creation. Reward2/4/5 and nonempty lasers remain unported.';
for(const path of ['cpp/game/EnemyTh16Commands.cpp','cpp/game/EnemyScript.cpp'])report.sourceHashes[path]=sha(readFileSync(resolve(rt,path)));writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(`PASS ${proof.cases.length} TH16 cancellation consumers, ${proof.circles.length} circle cases and ${report.ecl616RoutedCases} routed ECL616 cases`);
