import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/child-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-child-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/child-native.json'),'utf8'));
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','AnmManager','Interpolation'].map(n=>`cpp/game/${n}.cpp`);
sources.push('tests/cpp/th14-child-fixture.cpp');
const wasm=resolve(out,'children.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
for(const row of proof.cases){
 const label=`op ${row.op} refs ${row.refs} inherited ${row.inherited} child program ${row.program}`;
 assert.equal(c.run(row.op,row.refs,row.inherited,row.program),0,label+' status');
 assert.deepEqual(Array.from({length:21},(_,i)=>c.word(i)>>>0),[+row.parent,row.layer,+row.flag24,+row.linked,+row.stopped,...row.variables],label+' child state');
 assert.deepEqual(Array.from({length:12},(_,i)=>c.real(i)),[...row.position,...row.script,...row.child,...row.rotation],label+' positions');
 assert.equal(c.overlay_registry(),+['0x47e9f0','0x47eab0'].includes(row.registry[0]),label+' registry');
}
assert.equal(c.nested_retirement(),0,'production ownership: nested child destruction and parent-slot reuse');
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,scope:'Native TH14 child initialization, linking and first script update with allocation/binding/registry boundaries controlled. Production nested ownership test is not a native destructor comparison.',
 nativeExecutableSha256:proof.executableSha256,cases:proof.cases.length,nestedOwnershipRegression:true,wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,...['AnmVm','AnmOpcodes','AnmManager'].map(n=>`cpp/game/${n}.hpp`)].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-child-native.py','tools/th14-child-check.mjs','tools/th-anm-handlers.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-child-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.cases} original TH14 child-creation/first-update cases and nested ownership regression.`);
