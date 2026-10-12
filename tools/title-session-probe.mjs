// Bring-up diagnostic using the actual production archive and session. A successful
// probe is only entry/update/draw evidence, never a claim that title-specific semantics match.
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const title=Number(process.argv[2]),frames=Number(process.argv[3]??120);
const held=Number(process.argv[4]??0);if(!Number.isInteger(held)||held<0||held>255)throw Error('invalid held buttons');
if(![12,13,14,16,17,18].includes(title))throw Error('supported engine titles: 12, 13, 14, 16, 17, 18');
if(!Number.isSafeInteger(frames)||frames<0||frames>60000)throw Error('invalid frame count');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,`artifacts/th${title}/session-probe`);
mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title',String(title)],{cwd:root,env,stdio:'inherit',windowsHide:true});
const engineBuild=JSON.parse(readFileSync(resolve(root,`runtimes/th13/th13_web/artifacts/cpp/engine-th${title}-build.json`),'utf8'));
const dir=resolve(root,`runtimes/th13/th13_web/artifacts/cpp/objects-th${title}`),wasm=resolve(out,'session.wasm');
const fixture='tests/cpp/title-session-probe-fixture.cpp';
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',`-DPORT_TITLE=${title}`,fixture,...readdirSync(dir).filter(n=>n.endsWith('.o')).map(n=>resolve(dir,n)),'-o',wasm],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const target=JSON.parse(readFileSync(resolve(root,title===12?'runtimes/th12/th12_web/target.json':`runtimes/th${title}/target.json`),'utf8'));
const dat=readFileSync(target.dataArchives[`th${title}.dat`].path),bytes=readFileSync(wasm);
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
if(c.build_title()!==title)throw Error('wrong engine title');
const string=p=>{const b=new Uint8Array(c.memory.buffer);return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
const p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);
let archiveOpened=false,started=false,updates=0,submissions=0,error='';
try{
 archiveOpened=!!c.open_archive(p,dat.length);if(!archiveOpened)throw Error('archive open failed');
 started=!!c.begin(1,0,0,1);if(!started)throw Error(string(c.error()));
 for(;updates<frames;++updates){if(!c.tick(held)||!c.draw())throw Error(string(c.error()));submissions+=c.value(4);if(c.phase()!==1){++updates;break;}}
}catch(e){error=e.message;}
const sha=b=>createHash('sha256').update(b).digest('hex');
const observedOpcodes=Object.fromEntries(Array.from({length:710},(_,n)=>n+300).map(op=>[op,c.opcode_count(op)]).filter(([,count])=>count));
const report={title,completeGame:false,archiveOpened,started,updates,requestedFrames:frames,held,submissions,error,stage:c.value(0),frame:c.value(1),opcode:c.value(2),anmError:c.value(3),bulletError:c.bullet_error(),bulletTransforms:title===16?Array.from({length:18},(_,n)=>c.bullet_transform(n)):undefined,phase:c.phase(),lastResource:string(c.last_file()),battle:Object.fromEntries(['enemies','created','section','damage','dialogueStarts','dialogueWaits','bossWaits','dialogueActive','dialogueSignal','playerLive','eclUpdates'].map((n,i)=>[n,c.battle_value(i)])),scope:'Production archive/session entry and update/draw only; explicit held button mask, no forced invulnerability. Shared legacy subsystems may not match this title. Neither bounded success nor compilation proves gameplay or native pixel equivalence.',archiveSha256:sha(dat),sessionSha256:sha(bytes),fixtureSha256:sha(readFileSync(resolve(rt,fixture))),engineBuild};
report.observedOpcodes=observedOpcodes;
writeFileSync(resolve(out,'result.json'),JSON.stringify(report,null,2)+'\n');
const {engineBuild:metadata,...summary}=report;console.log(JSON.stringify(summary));if(error)process.exitCode=1;
