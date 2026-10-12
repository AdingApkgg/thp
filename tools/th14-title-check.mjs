import assert from 'node:assert/strict';
import {nativePython} from './native-python.mjs';
import {readFileSync,mkdirSync,writeFileSync,readdirSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/title-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
nativePython('tools/th14-title-native.py',{cwd:root,stdio:'inherit',windowsHide:true});
execFileSync(process.execPath,[resolve(root,'runtimes/th13/th13_web/scripts/cpp/build-engine.mjs'),'--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objectDir=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14');
const objects=readdirSync(objectDir).filter(n=>n.endsWith('.o')).map(n=>resolve(objectDir,n)),path=resolve(out,'title.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576','-DPORT_TITLE=14',
 'tests/cpp/th14-title-fixture.cpp',...objects,'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,sha=b=>createHash('sha256').update(b).digest('hex');
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json'),'utf8')),resourceHashes={};
for(const [i,name] of ['title.anm','title_v.anm','ascii.anm'].entries()){
 const row=archive.decoded.find(r=>r.name===name),b=readFileSync(resolve(archive.extraction,name));assert.equal(sha(b),row.sha256);resourceHashes[name]=row.sha256;
 const p=c.allocate(b.length);try{new Uint8Array(c.memory.buffer,p,b.length).set(b);assert.equal(c.open_resource(i,p,b.length),1,name);}finally{c.release(p);}
}
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/title-native.json'),'utf8'));
for(const row of proof.cases){
 const label=JSON.stringify(row);assert.equal(c.main_case(row.unlocked,row.selected,row.substate,row.timer,row.pressed,row.repeat),1,label);
 assert.deepEqual([0,1,2,5,6].map(k=>c.state(k)),[row.resultScreen,row.resultSubstate,row.resultSelected,row.difficulty,row.flags],label);
 assert.deepEqual(Array.from({length:c.state(4)},(_,i)=>c.sound(i)),row.sounds,label+' sounds');
}
for(const row of proof.selectionCases){
 const label=JSON.stringify(row);assert.equal(c.selection_case(row.kind,row.difficulty,row.character,row.selected,row.substate,row.timer,row.pressed,row.repeat),1,label);
 assert.deepEqual([0,1,2,3,5,10,11].map(k=>c.state(k)),row.state,label);
 assert.deepEqual(Array.from({length:c.state(4)},(_,i)=>c.sound(i)),row.sounds,label+' sounds');
}
const tick=(p=0,r=0)=>assert.equal(c.tick(p,r),1,'menu/ANM tick');
c.reset();tick();assert.equal(c.script_in_slot(86),86);assert.equal(c.script_in_slot(91),91);
for(let i=1;i<=180;++i)tick();assert.equal(c.script_in_slot(0),0);assert.equal(c.script_in_slot(306),0);
for(let i=0;i<20&&c.state(1)!==2;++i)tick();assert.equal(c.state(1),2);assert.equal(c.state(3),10);
tick(32);assert.equal(c.state(2),2);tick(16);assert.equal(c.state(2),0);tick(2);assert.equal(c.state(2),9);
const until=(screen,substate,limit=250)=>{for(let i=0;i<limit&&(c.state(0)!==screen||c.state(1)!==substate);++i)tick();assert.equal(c.state(0),screen);assert.equal(c.state(1),substate);};
for(let character=0;character<3;++character)for(let partner=0;partner<2;++partner){
 c.reset();until(1,2);tick(1);until(5,2);assert.equal(c.script_in_slot(114),114);assert.equal(c.script_in_slot(93),93);
 tick(1);until(6,2);assert.equal(c.script_in_slot(125),125);assert.equal(c.state(3),3);
 tick(2);until(5,2);tick(1);until(6,2);
 for(let i=0;i<character;++i){tick(128);tick();}tick(1);until(7,2);assert.equal(c.state(3),2);assert.equal(c.script_in_slot(126+character),126+character);
 tick(2);until(6,2);tick(1);until(7,2);
 if(partner)tick(128);tick(1);until(2,0,50);assert.equal(c.state(7),1);assert.equal(c.state(10),character);assert.equal(c.state(11),partner);assert.equal(c.state(8),1);
}
const report={passed:true,scope:'Retail main-menu, difficulty, character and equipment input/routing and sound events; six ordinary start paths with original ANM execution and return navigation. Controlled Extra eligibility uses native CR+7dc flags; actual4591d0/459220 eligibility is covered separately by th14-title-unlock-verified.json. Retail score import, saved clear badges, practice/replay modes, other menu screens, GPU pixels and complete gameplay are not verified.',
 nativeCases:proof.cases.length,selectionCases:proof.selectionCases.length,normalStartPaths:6,nativeExecutableSha256:proof.executableSha256,resourceHashes,wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries(['TitleTh14.cpp','TitleMenu.cpp','TitleMenu.hpp','TitleSelection.cpp','MenuCursor.cpp'].map(p=>[p,sha(readFileSync(resolve(rt,'cpp/game',p)))])),
 toolHashes:Object.fromEntries(['tools/th14-title-native.py','tools/th14-title-check.mjs','runtimes/th12/th12_web/tests/cpp/th14-title-fixture.cpp'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-title-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${proof.cases.length} main-menu / ${proof.selectionCases.length} selection inputs/routes; six normal start paths with original ANM and return navigation.`);
