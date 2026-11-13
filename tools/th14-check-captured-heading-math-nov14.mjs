import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/ordinary-difficulties-nov14');
const out=resolve(H,'stage3-heading-math-component-v2');assert.ok(!existsSync(out));mkdirSync(out);
const capture=readFileSync(resolve(H,'marisab-lunatic-stage3-collision-boundaries-v2/stage3-collision-queries.u32'));
const native=JSON.parse(readFileSync(resolve(H,'stage3-heading-retail-oracle.json')));
const sha=b=>createHash('sha256').update(b).digest('hex');assert.equal(native.captureSha256,sha(capture));
const fixture=resolve(out,'fixture.cpp');writeFileSync(fixture,`#include "Movement.hpp"
#include <cstring>
using namespace th11;
extern "C" __attribute__((export_name("run"))) const u32* run(float a,float length){
 const Vec2 v=polar(a,length);static u32 out[3];std::memcpy(out,&v,8);out[2]=0;return out;
}\n`);
const movement=resolve(R,'runtimes/th12/th12_web/cpp/game/Movement.cpp'),wasm=resolve(out,'polar.wasm');
execFileSync(resolve(R,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),
 ['--target=wasm32-wasip1','-std=c++17','-DPORT_TITLE=14','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-I'+resolve(R,'runtimes/th12/th12_web/cpp/game'),
 fixture,movement,'-o',wasm],{env:{...process.env,TEMP:out,TMP:out},windowsHide:true,stdio:'pipe'});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}});
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const scratch=new Uint32Array(1),floats=new Float32Array(scratch.buffer),f=bits=>{scratch[0]=bits;return floats[0];};
const differences=[],storedDifferences=[];
for(const row of native.rows){
 const p=instance.exports.run(f(row.angleBits),f(row.speedBits));
 const actual=Array.from(new Uint32Array(instance.exports.memory.buffer,p,3));
 if(actual.some((v,i)=>v!==row.freshRetailVelocityBits[i]))differences.push({index:row.index,controlFrame:row.controlFrame,slot:row.slot,production:actual,native:row.freshRetailVelocityBits});
 if(actual.some((v,i)=>v!==row.capturedVelocityBits[i]))storedDifferences.push({index:row.index,controlFrame:row.controlFrame,slot:row.slot,productionRebuild:actual,stored:row.capturedVelocityBits});
}
const q={cases:native.cases,productionPolarVsFreshRetailDifferences:differences.length,
 differences:differences.slice(0,20),storedVelocityVsProductionRebuildDifferences:storedDifferences.length,
 storedDifferences:storedDifferences.slice(0,20),actualCurrentMovementCompiled:true,
 movementSha256:sha(readFileSync(movement)),wasmSha256:sha(bytes),captureSha256:sha(capture),
 originalWholeTrajectoryAccepted:false,gameLogicChanged:false,completeGame:false,toolSha256:sha(readFileSync(import.meta.filename))};
writeFileSync(resolve(out,'report.json'),JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({...q,differences:q.differences.slice(0,3),storedDifferences:q.storedDifferences.slice(0,3)}));
