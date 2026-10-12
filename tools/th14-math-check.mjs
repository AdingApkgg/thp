import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/math-check');
mkdirSync(out,{recursive:true});
nativePython('tools/th14-math-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/math-native.json'),'utf8'));
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','Interpolation'].map(n=>`cpp/game/${n}.cpp`);
sources.push('tests/cpp/th14-math-fixture.cpp');
const wasm=resolve(out,'math.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',wasm],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(wasm);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,view=new DataView(new ArrayBuffer(4));
const asFloat=v=>{view.setUint32(0,v,true);return view.getFloat32(0,true);};
const close=(a,b,label)=>assert.ok(Math.abs(a-b)<=Math.max(1e-6,Math.abs(b)*2.4e-7),`${label}: ${a} != ${b}`);
for(const row of proof.cases){
 const args=[...row.args];while(args.length<4)args.push(0);
 const label=`op ${row.op} refs ${row.refs} inputs ${row.initialInts} visual ${row.visual}`;
 assert.equal(c.run(row.op,row.refs,row.args.length,...args,...row.initialInts.slice(0,2),row.seed,row.visual),0,label+' return');
 row.integers.forEach((v,i)=>assert.equal(c.word(i)>>>0,v,label+` integer ${i}`));
 row.floats.forEach((v,i)=>close(c.real(i),v,label+` float ${i}`));
 row.outputArgs.forEach((v,i)=>{
  const floating=(row.op<=121&&(row.op&1))||(row.op>=123&&row.op<=131)||(row.op>=203&&(row.op&1)&&i<2);
  if(floating)close(asFloat(c.word(i+4)),asFloat(v),label+` inline float ${i}`);
  else assert.equal(c.word(i+4)>>>0,v,label+` inline word ${i}`);
 });
 assert.equal(c.word(8),row.next,label+' next instruction');
 assert.equal(c.real(4),row.timer+1,label+' timer');
 assert.equal(c.word(9),row.rngSeed,label+' script seed');
 assert.equal(c.word(10),row.rngCalls,label+' script calls');
 assert.equal(c.word(11),row.visualCalls,label+' visual calls');
}
const sha=b=>createHash('sha256').update(b).digest('hex');
const report={passed:true,scope:'TH14 arithmetic/random/branch instruction state and jump destinations; no rendering or complete-game equivalence.',
 nativeExecutableSha256:proof.executableSha256,cases:proof.cases.length,wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,...['AnmVm','AnmOpcodes','Rng','Timer'].map(n=>`cpp/game/${n}.hpp`)].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-math-native.py','tools/th14-math-check.mjs','tools/th-anm-handlers.py'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-math-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${report.cases} original TH14 arithmetic/random/branch cases.`);
