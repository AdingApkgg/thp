// Pair actual retail playback of a port-written intact campaign with ordinary
// production playback. No invulnerability or power override in either run.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const option=(name,fallback)=>{const i=process.argv.indexOf(name);return i<0?fallback:process.argv[i+1];},sha=b=>createHash('sha256').update(b).digest('hex');
const label=option('--label','');assert(/^[a-z0-9-]{0,64}$/.test(label));const out=resolve(root,'artifacts/th14/custom-replay-reference',label||'baseline');mkdirSync(out,{recursive:true});
const tracePath=resolve(root,option('--native','artifacts/th14/native-campaign-reference-oct11.json')),traceBytes=readFileSync(tracePath),native=JSON.parse(traceBytes);
const manifestPath=resolve(root,option('--manifest','artifacts/th14/native-campaign-assets/57d84a5cbe82-cd2f2e3549c0/manifest.json')),manifestBytes=readFileSync(manifestPath),manifest=JSON.parse(manifestBytes);
assert.equal(manifest.passed,true);assert.equal(manifest.unchangedEntries,226);assert.equal(native.error,'');assert(native.frames.length>0);assert.equal(native.files.find(x=>x.name==='th14.dat').sha256,manifest.referenceArchiveSha256);
const replay=readFileSync(manifest.replayPath);assert.equal(sha(replay),manifest.replaySha256);
const selection=Number(option('--selection',0)),difficulty=Number(option('--difficulty',1));assert(Number.isInteger(selection)&&selection>=0&&selection<6);assert(Number.isInteger(difficulty)&&difficulty>=0&&difficulty<=4);assert.deepEqual(native.frames[0].selection,[Math.floor(selection/2),selection%2,difficulty,difficulty===4?7:1],'native actually selected the replaced complete campaign');
assert(native.frames.every(r=>JSON.stringify(r.selection)===JSON.stringify(native.frames[0].selection)),'do not combine distinct attract selections');
const engine=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')));
for(const [name,hash] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),hash,'changed engine '+name);
const fixture='tests/cpp/th14-natural-shot-diagnostic-fixture.cpp',objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),wasm=resolve(out,'reference.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',wasm],{cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
const bytes=readFileSync(wasm),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const upload=b=>{const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);return p;},target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.begin_custom_reference(upload(replay),replay.length),1);
const keys=['stageFrame','held','pressed','x','y','lifeState','stateAge','transitionAge','shootingAge','invincibility','shotAge','focused','score','graze','pointValue','power','lives','lifePieces','bombs','bombPieces','rank','scriptSeed','scriptCalls','replaySeed','replayCalls','enemyCount','shots','character','subtype','difficulty','stage','scaleFlags'];
const normalize=n=>{const g=n.globals,p=n.player;return [n.stageFrame,n.held,n.pressed,...p.slice(0,9),g[2],g[6],g[9],g[12],g[15],g[16],g[18],g[19],g[5],n.scriptRng[0],n.scriptRng[2],n.replayRng[0],n.replayRng[2],n.enemyCount,n.shots,...n.selection,n.scaleFlags].map(x=>x>>>0);};
const words=(p,n)=>Array.from(new Uint32Array(c.memory.buffer,p,n));
for(let frame=1;frame<=244;frame++){assert.equal(c.tick(0),1);assert.equal(c.draw(),1);if(frame>=242)console.log(JSON.stringify({frame,reference:words(c.reference_data(),32),slots:[232,235,236,239,255].map(slot=>({slot,details:Array.from({length:21},(_,i)=>c.natural_shot_detail(slot,i))}))}));}
