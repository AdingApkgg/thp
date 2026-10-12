import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/sprite-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-sprite-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/sprite-native.json'),'utf8'));
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','Interpolation'].map(n=>`cpp/game/${n}.cpp`);
sources.push('tests/cpp/th14-sprite-fixture.cpp');
const wasm=resolve(out,'sprites.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
for(const row of proof.cases){
 const label=`op ${row.op} sprite ${row.value} refs ${row.refs} callback ${row.callback} frame ${row.frame} seed ${row.seed} bound ${row.bound}`;
 assert.equal(c.run(row.value,row.refs,row.callback,row.frame,row.op,row.bound,row.seed),0,label+' status');
 assert.deepEqual(Array.from({length:5},(_,i)=>c.word(i)),[row.index,+row.fallback,+row.ownerUnchanged,+row.visible,row.spriteFrame],label);
 assert.deepEqual(Array.from({length:58},(_,i)=>c.real(i)),[...row.size,...row.uv,...row.matrix,...row.transform,...row.uvMatrix],label+' geometry');
 assert.deepEqual([c.rng(0),c.rng(1)],[row.rngSeed,row.rngCalls],label+' RNG');
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,scope:'Native TH14 sprite binding, callback and ASCII fallback resource selection with synthetic sprite tables; no GPU/render equivalence.',
 nativeExecutableSha256:proof.executableSha256,cases:proof.cases.length,wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,...['AnmVm','AnmOpcodes'].map(n=>`cpp/game/${n}.hpp`)].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-sprite-native.py','tools/th14-sprite-check.mjs','tools/th-anm-handlers.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-sprite-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.cases} original TH14 sprite bindings.`);
