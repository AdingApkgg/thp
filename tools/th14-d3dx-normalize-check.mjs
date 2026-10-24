import assert from 'node:assert/strict';
import {readFileSync as read,writeFileSync as write,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/d3dx-normalize-check'),rt=resolve(root,'runtimes/th12/th12_web');mkdirSync(out,{recursive:true});
nativePython('tools/th14-d3dx-normalize-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const label=process.argv[2]?(process.argv[3]??'candidate'):'normalize';assert(/^[a-z0-9-]+$/.test(label));
const source=process.argv[2]?resolve(process.argv[2]):resolve(rt,'cpp/game/GraphicsMath.cpp'),wasm=resolve(out,label+'.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14','tests/cpp/th14-d3dx-normalize-fixture.cpp',source,'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out},stdio:'inherit',windowsHide:true});
const proof=JSON.parse(read(resolve(out,'native.json'))),bytes=read(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const differences=[];for(const [words,expected]of proof.rows){c.run(...words);const actual=Array.from({length:3},(_,i)=>c.word(i)>>>0);if(actual.some((x,i)=>x!==expected[i]))differences.push({words,actual,expected});}
const sha=b=>createHash('sha256').update(b).digest('hex'),report={passed:differences.length===0,cases:proof.rows.length,differences,wasmSha256:sha(bytes),sourceSha256:sha(read(source)),dllSha256:proof.dllSha256,processor:proof.processor,actualWindowsX86Dll:true,finiteInputsOnly:true,completeGame:false,nativeEquivalent:false,scope:'Independent finite-vector controls through the actual x86 D3DX9_43 DLL on the recorded Windows reference CPU. Small/zero/signed-zero/axis/diagonal/camera vectors and 8192 seeded random vectors span exponents -100..60. Scalar SSE products/sums, small-vector zeroing and CPU reciprocal-square-root estimate plus refinement are compared bit for bit. Other CPU estimate implementations, nonfinite vectors, GPU pixels and complete gameplay are not certified.'};
write(resolve(out,process.argv[2]?label+'-report.json':'report.json'),JSON.stringify(report,null,2)+'\n');assert(report.passed,JSON.stringify(differences.slice(0,4)));
if(!process.argv[2])write(resolve(root,'docs/porting/th14-d3dx-normalize-verified-oct24.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS '+report.cases+' Windows x86 D3DX normalization controls.');
