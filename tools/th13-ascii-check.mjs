import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {nativePython} from './native-python.mjs';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th13/ascii-check');
mkdirSync(out,{recursive:true});
nativePython(resolve(root,'tools/th13-ascii-native.py'),{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th13/ascii-native.json'),'utf8'));
const sha=b=>createHash('sha256').update(b).digest('hex');
const sources=['cpp/game/AsciiText.cpp','cpp/game/AnmVm.cpp','tests/cpp/th13-ascii-fixture.cpp'];
const results=[];
for(const title of [13,12]){
 const path=resolve(out,`th${title}.wasm`);
 execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),[
  '--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti',
  '-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory',`-DPORT_TITLE=${title}`,...sources,'-o',path],
  {cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),bytes=readFileSync(path);
 const {instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);
 const c=instance.exports;
 const run=(text,font,sx=1,sy=1,shadow=0)=>{
  const b=Buffer.from(text+'\0'),p=c.allocate(b.length);
  try{new Uint8Array(c.memory.buffer,p,b.length).set(b);return c.run(p,font,sx,sy,shadow);}finally{c.release(p);}
 };
 let glyphs=0;
 if(title===13){
  for(const row of proof.cases){
   const label=`font ${row.font} scale ${row.scale} shadow ${row.shadow} ${JSON.stringify(row.text)}`;
   assert.equal(run(row.text,row.font,...row.scale,Number(row.shadow)),row.glyphs.length,label);
   row.glyphs.forEach((g,i)=>{
    for(const [k,key] of ['sprite','color','filtered'].entries())assert.equal(c.word(i,k)>>>0,Number(g[key]),`${label} glyph ${i} ${key}`);
    assert.equal(c.real(i,0),g.x,`${label} glyph ${i} x`);assert.equal(c.real(i,1),g.y,`${label} glyph ${i} y`);
   });glyphs+=row.glyphs.length;
  }
  assert.equal(run('0',8),-1);assert.equal(run('0',-1),-1);
 }else{
  assert.equal(run('012. /s',3),6);
  [243,244,245,254,253,255].forEach((v,i)=>assert.equal(c.word(i,0),v));
  assert.equal(c.real(4,0),76.25);assert.equal(run('0',4),-1);
  assert.equal(run('+$',2),2);assert.equal(c.word(0,0),238);assert.equal(c.word(1,0),260);
 }
 results.push({title,passed:true,glyphs,wasmSha256:sha(bytes)});
}
const report={passed:true,nativeExecutableSha256:proof.executableSha256,nativeStringCases:proof.cases.length,
 scope:'ASCII glyph selection, positions, filtering and shadows; not GPU pixel equivalence or complete HUD behavior.',results,
 sourceHashes:Object.fromEntries([...sources,'cpp/game/AsciiText.hpp','cpp/game/PortTitle.hpp'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),
 toolHashes:Object.fromEntries(['tools/th13-ascii-native.py','tools/th13-ascii-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th13-ascii-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: ${proof.cases.length} native strings, ${results[0].glyphs} glyph submissions; TH12 font regression passed.`);
