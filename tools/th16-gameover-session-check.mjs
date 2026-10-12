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
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th16/gameover-session-check');
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

const checkpoints=[];const point=label=>checkpoints.push({label,phase:c.phase(),frame:c.value(1),menu:Array.from({length:5},(_,n)=>c.pause_value(n))});
const tick=(held=0)=>{assert.equal(c.tick_input(held,0),1,string(c.error()));assert.equal(c.draw(),1,string(c.error()));};
const step=(count,held=0)=>{for(let n=0;n<count;++n)tick(held);};
assert.equal(c.open_archive(p,dat.length),1);assert.equal(c.begin(1,0,0,1),1,string(c.error()));
let updates=0;for(;updates<60000&&c.phase()===1;++updates)tick(1);
assert.equal(c.phase(),3);point('game_over_entry');step(13);point('score_transition');
if(c.pause_value(1)===15){step(10);tick(16);tick();tick(64);tick();tick(1);point('name_finished');}
assert.equal(c.pause_value(1),6);if(c.pause_value(2)===0){tick(32);tick();}assert.equal(c.pause_value(2),1);tick(1);step(14);point('returned_to_title');assert.equal(c.phase(),0);
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th16-gameover-session-progress-oct10.json'),JSON.stringify({title:16,completeGame:false,updates,checkpoints,archiveSha256:sha(dat),wasmSha256:sha(bytes),engineBuild,scope:'Production TH16 archive: normal held shooting until natural game-over, score transition, name confirmation if ranked, end choices and title exit. No forced invulnerability. Actual ANM/draw submissions. Bounded integration; native pixels, disk score/replay saving, continue and full campaign excluded.'},null,2)+'\n');console.log(JSON.stringify({updates,checkpoints}));
