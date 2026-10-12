import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/flow-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-flow-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/flow-native.json'),'utf8'));
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','Interpolation'].map(n=>`cpp/game/${n}.cpp`);
sources.push('tests/cpp/th14-flow-fixture.cpp');
const wasm=resolve(out,'flow.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports;
for(const row of proof.cases){
 c.begin_case(row.wait,row.rate,Number(row.fallback));
 for(const [frame,e] of row.timeline.entries()){
  const label=`wait ${row.wait} rate ${row.rate} request ${row.request} fallback ${row.fallback} frame ${frame}`;
  assert.equal(c.tick(e.pending),e.status,label+' status');
  assert.deepEqual([c.word(0),!!c.word(1),!!c.word(2),c.word(3)>>>0,c.word(4),c.real(0),c.real(1)],
   [e.instruction,e.visible,e.waiting,e.primary,e.savedInstruction,e.timer,e.savedTimer],label);
 }
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,scope:'TH14 wait, hide/wait, interrupt selection/fallback and return timelines; no complete-game equivalence.',
 nativeExecutableSha256:proof.executableSha256,timelines:proof.cases.length,frames:proof.cases.reduce((n,r)=>n+r.timeline.length,0),wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,...['AnmVm','AnmOpcodes','Timer'].map(n=>`cpp/game/${n}.hpp`)].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-flow-native.py','tools/th14-flow-check.mjs','tools/th-anm-handlers.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-flow-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.timelines} original TH14 interrupt timelines (${report.frames} frames).`);
