import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th13/title-check');
mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync('py',['-3',resolve(root,'tools/th13-title-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,[resolve(root,'runtimes/th13/th13_web/scripts/cpp/build-engine.mjs')],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objectDir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th13');
const objects=readdirSync(objectDir).filter(n=>n.endsWith('.o')).map(n=>resolve(objectDir,n));
const path=resolve(out,'title.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=13',
 'tests/cpp/th13-title-fixture.cpp',...objects,'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,sha=b=>createHash('sha256').update(b).digest('hex');
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th13.json'),'utf8'));
const resourceHashes={};
for(const [i,name] of ['title.anm','title_v.anm','ascii.anm'].entries()){
 const row=archive.decoded.find(r=>r.name===name),b=readFileSync(resolve(archive.extraction,name));
 assert.equal(sha(b),row.sha256);resourceHashes[name]=row.sha256;
 const p=c.allocate(b.length);try{new Uint8Array(c.memory.buffer,p,b.length).set(b);assert.equal(c.open_resource(i,p,b.length),1,name);}finally{c.release(p);}
}
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th13/title-native.json'),'utf8'));
for(const row of proof.cases){
 const label=JSON.stringify(row);assert.equal(c.character_case(row.difficulty,row.selected,row.pressed,row.repeat),1,label);
 assert.equal(c.state(2),row.resultSelected,label+' selection');assert.equal(c.state(1),row.substate,label+' substate');
 assert.deepEqual(Array.from({length:c.state(4)},(_,i)=>c.sound(i)),row.sounds,label+' sounds');
}
const tick=(p=0,r=0)=>assert.equal(c.tick(p,r),1,'menu/ANM tick');
const until=(screen,substate,limit=250)=>{for(let i=0;i<limit&&(c.state(0)!==screen||c.state(1)!==substate);++i)tick();assert.equal(c.state(0),screen);assert.equal(c.state(1),substate);};
for(let character=0;character<4;++character){
 c.reset();tick();assert.equal(c.script_in_slot(79),89);assert.equal(c.script_in_slot(83),94);
 until(1,2);assert.equal(c.script_in_slot(0),0);
 tick(1);until(5,2);assert.equal(c.script_in_slot(96),101);assert.equal(c.script_in_slot(123),123);
 tick(1);until(6,2);assert.equal(c.state(3),4);assert.equal(c.script_in_slot(129),129);
 // Return once, preserving the difficulty/character cursor stack.
 tick(2);until(5,2);tick(1);until(6,2);
 for(let i=0;i<character;++i){tick(128);tick();}
 assert.equal(c.state(2),character);tick(1);until(2,0,50);
 assert.equal(c.state(7),1);assert.equal(c.state(5),character);assert.equal(c.state(6),0);assert.equal(c.state(8),1);
}
const sources=['TitleMenu.cpp','TitleSelection.cpp','AsciiText.cpp','Hud.cpp','PortTitle.hpp'];
const report={passed:true,scope:'Native character input states and sounds; four normal-game title paths with original ANM resources. Remaining title screens and complete gameplay are not verified.',
 nativeCases:proof.cases.length,nativeExecutableSha256:proof.executableSha256,characterStartPaths:4,resourceHashes,wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,'cpp/game',p)))])),
 toolHashes:Object.fromEntries(['tools/th13-title-native.py','tools/th13-title-check.mjs','runtimes/th12/th12_web/tests/cpp/th13-title-fixture.cpp'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th13-title-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${proof.cases.length} original character inputs; four normal-game start paths and return navigation.`);
