import assert from 'node:assert/strict';
// Bring-up diagnostic using the actual production archive and session. A successful
// probe is only entry/update/draw evidence, never a claim that title-specific semantics match.
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const title=16,frames=0;
const frameArg=process.argv.indexOf('--frames'),limit=frameArg>=0?Number(process.argv[frameArg+1]):240;
assert.ok(Number.isInteger(limit)&&limit>=240&&limit<=60000,'frames must be 240..60000');
const held=0;if(!Number.isInteger(held)||held<0||held>255)throw Error('invalid held buttons');
if(![12,13,14,16,17,18].includes(title))throw Error('supported engine titles: 12, 13, 14, 16, 17, 18');
if(!Number.isSafeInteger(frames)||frames<0||frames>60000)throw Error('invalid frame count');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/season-shot-session-check');
mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title',String(title)],{cwd:root,env,stdio:'inherit',windowsHide:true});
const engineBuild=JSON.parse(readFileSync(resolve(root,`runtimes/th13/th13_web/artifacts/cpp/engine-th${title}-build.json`),'utf8'));
const dir=resolve(root,`runtimes/th13/th13_web/artifacts/cpp/objects-th${title}`),wasm=resolve(out,'session.wasm');
const fixture='tests/cpp/th16-options-session-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',`-DPORT_TITLE=${title}`,fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const target=JSON.parse(readFileSync(resolve(root,title===12?'runtimes/th12/th12_web/target.json':`runtimes/th${title}/target.json`),'utf8'));
const dat=readFileSync(target.dataArchives[`th${title}.dat`].path),bytes=readFileSync(wasm);
async function fresh(){
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 if(c.build_title()!==title)throw Error('wrong engine title');
 const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
 const p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
 return {c,string};
}
const cases=[];
const sha=b=>createHash('sha256').update(b).digest('hex');
for(let character=0;character<4;character++)for(let season=0;season<5;season++){
 const {c,string}=await fresh();
 const run={character,season,updates:0,main:0,seasonal:0,phase:1,passed:false,error:''};cases.push(run);
 try{
  assert.equal(c.begin_season(character,season),1,string(c.error()));assert.equal(c.upgrade(400,1140),1,'upgrade');
  for(;run.updates<limit;run.updates++){
   assert.equal(c.tick_input(1|(run.updates>=120?8:0),0),1,string(c.error()));assert.equal(c.draw(),1,string(c.error()));assert.equal(c.shots_valid(),1,'shot ANM family/position mismatch');
   run.main=Math.max(run.main,c.shots_count(0));run.seasonal=Math.max(run.seasonal,c.shots_count(1));
   run.phase=c.phase();if(run.phase!==1){++run.updates;break;}
  }
  assert.ok(run.main>0&&run.seasonal>0,'both families must emit shots');run.passed=true;
 }catch(error){run.error=error.message;if(!(error instanceof WebAssembly.RuntimeError))run.bulletDiagnostic=Array.from({length:22},(_,n)=>c.bullet_diagnostic(n));}
}
const report={title:16,completeGame:false,frameLimit:limit,cases,archiveSha256:sha(dat),wasmSha256:sha(bytes),engineBuild,scope:'Actual production archive and own PlayerFrame/ShotManager paths, four characters/five explicitly selected resource families, synthetic maximum power/season energy, shooting updates until configured limit or phase change with focus switch at120, own ANM family/file/position checks and draw submissions, observed main/season live shots. Reports each failure without marking it passed. No forced invulnerability; UI selection, natural progression, native pixels and full game excluded.'};
writeFileSync(resolve(root,limit===240?'docs/porting/th16-season-shot-session-progress-oct10.json':'docs/porting/th16-season-shot-session-long-progress-oct10.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(cases));assert.ok(cases.every(c=>c.passed),'Some actual-resource seasonal shooting cases failed; see report');
