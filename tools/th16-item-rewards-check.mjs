import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/item-rewards-check');mkdirSync(out,{recursive:true});
nativePython('tools/th16-item-rewards-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','16'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th16'),wasm=resolve(out,'item-rewards.wasm'),fixture='tests/cpp/th16-item-rewards-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=16',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th16/item-rewards-native.json'),'utf8'));
const compare=r=>{assert.deepEqual(Array.from({length:14},(_,n)=>c.value(n)>>>0),r.output,JSON.stringify(r));assert.deepEqual(Array.from({length:c.event_count()},(_,n)=>c.event(n)>>>0),r.events,JSON.stringify(r));};
for(const r of proof.scores){assert.equal(c.score_case(r.score,r.amount,r.difficulty,r.extend,r.lives,r.fragments),1,JSON.stringify(r));compare(r);}
for(const r of proof.stocks){assert.equal(c.stock_case(r.kind,r.count,r.fragments),r.kind===0?r.awarded:1,JSON.stringify(r));compare(r);}
for(const r of proof.pickups){assert.equal(c.pickup_case(r.kind,r.power,r.point,r.character,r.y,r.state),1,JSON.stringify(r));compare(r);}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-item-rewards-verified.json'),JSON.stringify({passed:true,title:16,completeGame:false,scoreCases:proof.scores.length,stockCases:proof.stocks.length,pickupCases:proof.pickups.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Full finite own43e080/43ddd0 score and extend loops,43df70 life,43dfb0 bomb,43dff0 fragment and42fd84 ordinary pickup dispatch through42fe9d, including430100/4303a0/4304a0/430620. Delivery of HUD, audio, popup and option rebuild controlled. Compare economy fields and ordered service requests. Score inputs beyond the final sentinel, production option rebuild/HUD consumers, physical audio, draw and full gameplay excluded.',sourceHashes:Object.fromEntries(['cpp/game/ItemRewards.cpp','cpp/game/ItemRewards.hpp','cpp/game/GameEconomy.hpp',fixture].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');console.log(`PASS ${proof.scores.length} score/extend, ${proof.stocks.length} stocks, ${proof.pickups.length} ordinary pickups`);
