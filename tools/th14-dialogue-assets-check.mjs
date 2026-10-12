import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/dialogue-assets-check');mkdirSync(out,{recursive:true});
nativePython('tools/th14-dialogue-assets-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const dir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'dialogue.wasm'),fixture='tests/cpp/th14-dialogue-assets-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-assets-native.json'),'utf8'));let routes=0;
for(const r of proof.cases){assert.equal(c.asset(r.stage,r.selection,r.opcode),1);assert.deepEqual([c.word(0)>>>0,c.word(1)>>>0],[r.file>>>0,r.script],JSON.stringify(r));
 if(r.file<0){assert.equal(c.route(r.stage,r.selection,r.opcode),-2);continue;}
 assert.equal(c.route(r.stage,r.selection,r.opcode),0,JSON.stringify(r));assert.deepEqual(Array.from({length:5},(_,n)=>c.created_word(n)>>>0),[100+r.file,r.script,0x200,22,1],JSON.stringify(r));++routes;
}
for(const [stage,selection,op] of [[0,0,2],[8,0,20],[1,-1,2],[1,3,20],[1,0,3]])assert.equal(c.asset(stage,selection,op),0);
for(const r of proof.fades){assert.equal(c.route(r.stage,r.value|0,r.opcode),0,JSON.stringify(r));assert.deepEqual([c.fade_word(0),c.fade_word(1)>>>0],[1,r.result],JSON.stringify(r));}
for(const r of proof.speakerResets){assert.equal(c.speaker_reset(r.selection,r.flags,r.displacement),0,JSON.stringify(r));assert.deepEqual(Array.from({length:29},(_,n)=>c.reset_word(n)>>>0),[...r.state,r.interrupts[0][1],...r.lines.flat()],JSON.stringify(r));assert.deepEqual(r.interrupts,[[102,3]]);}
const sha=b=>createHash('sha256').update(b).digest('hex');writeFileSync(resolve(root,'docs/porting/th14-dialogue-assets-verified.json'),JSON.stringify({passed:true,cases:proof.cases.length,routes,musicFadeCases:proof.fades.length,speakerResetCases:proof.speakerResets.length,nativeExecutableSha256:proof.executableSha256,wasmSha256:sha(bytes),scope:'Retail MSG 2/20/31 stage and speaker resource/script selection, before ANM allocation. MSG 22/27 default and explicit music fade arguments are compared at the retail 445840 call boundary. Port MSG decoding and resource routing use real Dialogue/AnmManager with synthetic stop scripts. MSG 32 speaker/line reset writes and one portrait interrupt are compared through retail 433107..43369d with controlled ANM lookups. Retail allocation, ANM execution, other portrait expressions and speaker layout, HUD side effects and pixels are not asserted.',sourceHashes:Object.fromEntries([fixture,'cpp/game/Dialogue.cpp','cpp/game/Dialogue.hpp','cpp/game/GameBattle.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-dialogue-assets-native.py','tools/th14-dialogue-assets-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))},null,2)+'\n');console.log(`PASS: ${proof.cases.length} native selections, ${routes} MSG resource routes.`);
