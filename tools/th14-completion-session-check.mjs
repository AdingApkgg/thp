import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/completion-session-check');mkdirSync(out,{recursive:true});
const env={...process.env,TEMP:out,TMP:out,TMPDIR:out};
execFileSync(process.execPath,['runtimes/th13/th13_web/scripts/cpp/build-engine.mjs','--title','14'],{cwd:root,env,stdio:'inherit',windowsHide:true});
const objects=resolve(root,'runtimes/th13/th13_web/artifacts/cpp/objects-th14'),fixture='tests/cpp/th14-completion-session-fixture.cpp',path=resolve(out,'completion-session.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-DPORT_TITLE=14','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...readdirSync(objects).filter(n=>n.endsWith('.o')).map(n=>resolve(objects,n)),'-o',path],{cwd:rt,env,stdio:'inherit',windowsHide:true});
const bytes=readFileSync(path),target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'),'utf8')),dat=readFileSync(target.dataArchives['th14.dat'].path),rows=[];
for(let selection=0;selection<6;++selection)for(const continues of [0,1]){
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const p=c.allocate(dat.length);new Uint8Array(c.memory.buffer,p,dat.length).set(dat);assert.equal(c.open_archive(p,dat.length),1);
 const error=()=>{const b=new Uint8Array(c.memory.buffer),p=c.error();return new TextDecoder().decode(b.subarray(p,b.indexOf(0,p)));};
 assert.equal(c.begin(6,selection>>1,selection&1,1),1,error());assert.equal(c.finish_stage(continues),1,error());let frames=0;
 for(;frames<500&&c.phase()===1;++frames){assert.equal(c.combat_tick(0),1,error());assert.equal(c.draw(),1,error());
  if(frames===179)assert.deepEqual([5,6,7].map(k=>c.ending_value(k)),[73,200,5],'actual GameBattle fade matches retail registration/duration/type');
 }
 assert.equal(c.phase(),5,`ending route selection${selection}, continues${continues}: ${error()}`);
 assert.equal(c.ending_value(0),selection+(continues?7:1));
 let endingFrames=0;for(;endingFrames<30000&&c.phase()===5;++endingFrames){assert.equal(c.tick((endingFrames%2?0:1)|512),1,error());assert.equal(c.draw(),1,error());}
 assert.equal(c.phase(),0,`ending termination selection${selection}: ${error()}`);assert.equal(c.ending_value(2),14,'actual result menu after staff');
 rows.push({selection,continues,ending:`e${String(selection+(continues?7:1)).padStart(2,'0')}.msg`,transitionFrames:frames,endingFrames,passed:true});console.log(JSON.stringify(rows.at(-1)));
}
const sha=b=>createHash('sha256').update(b).digest('hex');
writeFileSync(resolve(root,'docs/porting/th14-completion-session-verified.json'),JSON.stringify({passed:true,rows,archiveSha256:sha(dat),wasmSha256:sha(bytes),scope:'Original resources, actual GameBattle MSG21 completion and GameSession ending/staff/result route for six equipment choices with and without continues. Stage completion boundary is invoked directly; player invulnerability controls the brief stage-to-ending wait. Does not prove a natural full campaign, retail ending interpreter/timing/GPU equivalence or browser storage.',sourceHashes:Object.fromEntries([fixture,'cpp/game/Ending.cpp','cpp/game/StageCompletion.cpp','cpp/game/GameBattle.cpp','cpp/game/GameSession.cpp'].map(n=>[n,sha(readFileSync(resolve(rt,n)))]))},null,2)+'\n');
console.log('PASS twelve original-resource ending/staff/result routes');
