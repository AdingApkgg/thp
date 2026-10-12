import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/position-check');
mkdirSync(out,{recursive:true});
execFileSync('py',['-3',resolve(root,'tools/th14-position-native.py')],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/position-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['AnmVm','AnmGeometry','AnmInterpreter','AnmResource','Interpolation'].map(n=>`cpp/game/${n}.cpp`).concat('tests/cpp/th14-position-fixture.cpp');
const path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
 '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
 '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],
 {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
const c=instance.exports,p=c.allocate(268);assert.ok(p);
let checked=0;
for(const [quad,rows] of [[0,proof.cases],[1,proof.quads]])for(const row of rows){
 new Float32Array(c.memory.buffer,p,60).set(row.nodes.flatMap(n=>[...n.position,...n.script,...n.child,...n.rotation,...n.size,...n.pivot,...n.scale,...n.extra]));
 new Uint32Array(c.memory.buffer,p+240,3).set(row.nodes.map(n=>n.flags));
 new Int32Array(c.memory.buffer,p+252,4).set(row.origins);
 assert.equal(c.run(row.depth,p,p+240,row.displayScale,p+252,row.mode,row.anchor,quad),0);
 for(const [i,want] of row.result.entries()){
  const actual=c.value(i),tolerance=Math.max(0.00001,Math.abs(want)*0.00000024);
  assert.ok(Math.abs(actual-want)<=tolerance,`${quad?'quad':'position'} ${checked}, field ${i}: ${actual} != ${want}; ${JSON.stringify(row)}`);
 }
 ++checked;
}
c.release(p);
const report={passed:true,nativeExecutableSha256:proof.executableSha256,nativePositionCases:proof.cases.length,nativeQuadCases:proof.quads.length,
 scope:'TH14 recursive parent translation/rotation, all resolution and origin selectors, and four query modes with nine anchors. Controlled display globals; D3D submission and display initialization are not asserted.',wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,'cpp/game/AnmVm.hpp','cpp/game/AnmGeometry.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th14-position-native.py','tools/th14-position-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-position-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${proof.cases.length} native TH14 positions and ${proof.quads.length} quad queries.`);
