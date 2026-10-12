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
const held=0;if(!Number.isInteger(held)||held<0||held>255)throw Error('invalid held buttons');
if(![12,13,14,16,17,18].includes(title))throw Error('supported engine titles: 12, 13, 14, 16, 17, 18');
if(!Number.isSafeInteger(frames)||frames<0||frames>60000)throw Error('invalid frame count');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/pause-session-check');
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

const checkpoints=[];
const tick=(held=0,pause=0)=>{assert.equal(c.tick_input(held,pause),1,string(c.error()));assert.equal(c.draw(),1,string(c.error()));};
const step=(count,held=0)=>{for(let n=0;n<count;++n)tick(held);};
const point=label=>checkpoints.push({label,phase:c.phase(),frame:c.value(1),menu:Array.from({length:5},(_,n)=>c.pause_value(n))});
assert.equal(c.open_archive(p,dat.length),1);assert.equal(c.begin(1,0,0,1),1,string(c.error()));step(120,1);point('stage_before_pause');
tick(0,1);step(12);point('pause_ready');assert.equal(c.phase(),2);assert.equal(c.pause_value(1),6);
tick(0,1);step(13);point('resumed');assert.equal(c.phase(),1);step(60,1);
tick(0,1);step(12);tick(32);tick();tick(1);step(30);point('title_confirmation');assert.equal(c.pause_value(1),7);assert.equal(c.pause_value(2),1);
tick(16);tick();tick(1);step(34);point('confirmed_title_exit');assert.equal(c.phase(),0);
assert.equal(c.begin(1,0,0,1),1,string(c.error()));step(120,1);tick(0,1);step(12);for(let n=0;n<4;++n){tick(32);tick();}assert.equal(c.pause_value(2),4);tick(1);step(30);point('restart_confirmation');tick(16);tick();tick(1);step(34);point('restarted');assert.equal(c.phase(),1);assert.ok(c.value(1)<20);
// The title screen and its resources are a separate consumer under development.
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-pause-session-progress-oct10.json'),JSON.stringify({title:16,completeGame:false,checkpoints,archiveSha256:sha(dat),wasmSha256:sha(bytes),engineBuild,scope:'Production TH16 archive, no forced invulnerability. Stage120 updates, pause delay, Esc resume, stage60 updates, title choice and confirmation, then a fresh run and restart confirmation. Render submits actual ANM. Bounded integration only; native pixel and title consumer equivalence excluded.'},null,2)+'\n');console.log(JSON.stringify(checkpoints));
