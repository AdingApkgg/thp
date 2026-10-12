import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th13/position-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th13-position-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th13/position-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmVm','AnmResource','AnmInterpreter','AnmManager','AnmGeometry','Interpolation'].map(n=>`cpp/game/${n}.cpp`).concat('tests/cpp/th13-position-fixture.cpp');
const results=[];
for(const title of [13,12]){
 const path=resolve(out,`th${title}.wasm`);
 execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
  '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
  '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',`-DPORT_TITLE=${title}`,...sources,'-o',path],
  {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
 const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
 const c=instance.exports,p=c.allocate(120);
 for(const row of proof.cases){
  new Float32Array(c.memory.buffer,p,27).set(row.nodes.flatMap(n=>[...n.position,...n.script,...n.child]));
  new Uint32Array(c.memory.buffer,p+108,3).set(row.nodes.map(n=>n.flags));
  c.position_case(row.depth,p,p+108);
  const expected=title===13?row.result:[0,1,2].map(i=>Math.fround(Math.fround(row.nodes[0].position[i]+row.nodes[0].script[i])+row.nodes[0].child[i]));
  assert.deepEqual([0,1,2].map(i=>c.position_value(i)),expected,JSON.stringify(row));
 }
 c.release(p);
 if(title===13){
  for(const [i,row] of proof.spawns.entries()){
   assert.equal(c.spawn_case([500,501,502,503,504][i]),0);
   assert.deepEqual(Array.from({length:9},(_,i)=>c.spawn_real(i)),[...row.position,...row.child,...row.rotation]);
   assert.equal(c.spawn_word(0),row.layer);assert.equal(c.spawn_word(1),Number(row.parent));
   assert.equal(c.spawn_word(2),['0x46f540','0x46f5f0'].includes(row.registry[0])?1:0);
   assert.equal(c.parent_move(),row.detached?15:115,'attached animations follow later parent movement');
   assert.equal(c.parent_destroy(),row.detached?1:0,'attached animations retire with their parent');
  }
  assert.equal(c.nested_retirement(),0,'three-generation chain survives creation and retires before parent reuse');
 }
 results.push({title,passed:true,wasmSha256:sha(bytes)});
}
const report={passed:true,nativeExecutableSha256:proof.executableSha256,nativePositionCases:proof.cases.length,nativeSpawnCases:proof.spawns.length,
 scope:'2D recursive ANM translation, creation registry selection, detached copies, live parent movement and parent retirement. Full 3D parent transforms and gameplay are not asserted.',results,
 sourceHashes:Object.fromEntries([...sources,'cpp/game/AnmVm.hpp','cpp/game/AnmManager.hpp','cpp/game/AnmOpcodes.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th13-position-native.py','tools/th13-position-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th13-position-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${proof.cases.length} native positions and ${proof.spawns.length} child creation variants; TH12 translation regression.`);
