import assert from'node:assert/strict';
import{readFileSync as read,writeFileSync as write,mkdirSync as mkdir}from'node:fs';
import{resolve}from'node:path';import{createHash}from'node:crypto';import{execFileSync}from'node:child_process';import{WASI}from'node:wasi';import{nativePython}from'./native-python.mjs';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/anm-scale-velocity-check'),sha=b=>createHash('sha256').update(b).digest('hex');mkdir(out,{recursive:true});
nativePython('tools/th14-anm-scale-velocity-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const sources=['AnmInterpreter','AnmVm','AnmGeometry','Interpolation','AnmResource'].map(s=>'cpp/game/'+s+'.cpp'),fixture='tests/cpp/th14-anm-scale-velocity-fixture.cpp',wasm=resolve(out,'probe.wasm');
execFileSync(resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',...sources,fixture,'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const proof=JSON.parse(read(resolve(out,'native.json'))),bytes=read(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
assert(proof.originalInstructionsUnmodified);assert.equal(proof.cases.length,144);
for(const [index,row]of proof.cases.entries()){
 assert.equal(c.run(row.seed,row.visualSeed,row.refs,row.initialFlags2,...row.argsBits),0,'case '+index);
 assert.deepEqual(Array.from({length:7},(_,i)=>c.word(i)>>>0),row.values,JSON.stringify({index,...row}));
}
const tracked=[...sources,...['AnmVm','AnmOpcodes','AnmResource','AnmGeometry','Interpolation','Timer','Rng','Types','PortTitle'].map(s=>'cpp/game/'+s+'.hpp'),fixture];
const report={passed:true,originalExecutableSha256:proof.originalExecutableSha256,originalHandler:proof.originalHandler,originalInstructionsUnmodified:true,controlledVmAndSeeds:true,handlerOnlyNotCompleteProcess:true,cases:144,comparedValues:['flags2','scaleVelocityXBits','scaleVelocityYBits','scriptSeed','scriptCalls','visualSeed','visualCalls'],wasmSha256:sha(bytes),nativeProofSha256:sha(read(resolve(out,'native.json'))),sourceHashes:Object.fromEntries(tracked.map(p=>[p,sha(read(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-anm-scale-velocity-native.py','tools/th14-anm-scale-velocity-check.mjs'].map(p=>[p,sha(read(resolve(root,p)))])),completeGame:false,nativeEquivalent:false};
write(resolve(root,'docs/porting/th14-anm-scale-velocity-verified-oct24.json'),JSON.stringify(report,null,2)+'\n');write(resolve(out,'report.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS: 144 original TH14 scale-velocity handler cases; Y/X reference order, flag and RNG state.');
