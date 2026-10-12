import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/variables-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-variables-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/variables-native.json'),'utf8'));
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','Interpolation'].map(n=>`cpp/game/${n}.cpp`);
sources.push('tests/cpp/th14-variables-fixture.cpp');
const wasm=resolve(out,'variables.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
for(const row of proof.cases){
 const label=`kind ${row.kind} variable ${row.value} bound ${row.bound} parent ${row.parent}`;
 c.run(row.kind,row.value,row.bound,row.parent);
 assert.equal(c.value(),row.result,label);
 assert.deepEqual(Array.from({length:4},(_,i)=>c.rng(i)),[row.scriptSeed,row.scriptCalls,row.visualSeed,row.visualCalls],label+' RNG');
}
const sha=b=>createHash('sha256').update(b).digest('hex');
for(const [seed,row] of proof.rngSamples.entries())for(let signed=0;signed<2;++signed){
 assert.equal(c.rng_case(seed,signed),row[signed],`seed ${seed} signed ${signed}`);
 assert.deepEqual([c.rng(0),c.rng(1)],row.slice(2),`seed ${seed} RNG state`);
}
const report={passed:true,scope:'TH14 ANM integer/float reads and writable destination selection, including script/visual RNG; native globals are controlled fixture inputs.',
 nativeExecutableSha256:proof.executableSha256,cases:proof.cases.length,rngSeeds:proof.rngSamples.length,rngResults:proof.rngSamples.length*2,wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,...['AnmVm','AnmOpcodes','Rng'].map(n=>`cpp/game/${n}.hpp`)].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-variables-native.py','tools/th14-variables-check.mjs','tools/th-anm-handlers.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-variables-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.cases} original TH14 variable-access cases; ${report.rngResults} RNG results across all ${report.rngSeeds} seeds.`);
