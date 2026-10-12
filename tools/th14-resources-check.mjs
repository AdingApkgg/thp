import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/resources-check');mkdirSync(out,{recursive:true});
for(const tool of ['th14-sht-native.py','th14-audio-table.py'])execFileSync('py',['-3',resolve(root,'tools',tool)],{cwd:root,stdio:'inherit',windowsHide:true});
const proof=JSON.parse(readFileSync(resolve(root,'artifacts/th14/sht-native.json'),'utf8'));
const audio=JSON.parse(readFileSync(resolve(root,'docs/porting/th14-audio-table-verified.json'),'utf8'));
const sources=['cpp/game/ShtResource.cpp','cpp/game/SoundEffects.cpp','tests/cpp/th14-resources-fixture.cpp'],path=resolve(out,'th14.wasm');
execFileSync(resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-DPORT_TITLE=14',...sources,'-o',path],{cwd:rt,stdio:'inherit',windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out}});
const bytes=readFileSync(path),wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(bytes,{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json'),'utf8')),sha=b=>createHash('sha256').update(b).digest('hex');
let shots=0,groups=0,negative=0;
for(const f of proof.files){
 const b=readFileSync(resolve(archive.extraction,f.name));assert.equal(sha(b),f.sha256);const p=c.allocate(b.length);new Uint8Array(c.memory.buffer,p,b.length).set(b);
 assert.equal(c.open_sht(p,b.length),1,f.name);assert.equal(c.group_count(),f.groups.length);
 assert.equal(Buffer.from(c.memory.buffer,c.header_data(),0xe0).toString('hex'),f.header);
 f.groups.forEach((g,i)=>{
  ++groups;assert.equal(c.shot_count(i),g.records.length);
  g.records.forEach((want,j)=>{
   const actual=Buffer.from(new Uint8Array(c.memory.buffer,c.shot_data(i,j),0x58));
   for(const [offset,table] of Object.entries(proof.callbackTables)){const index=actual.readUInt32LE(Number(offset));assert.ok(String(index) in table);actual.writeUInt32LE(table[index],Number(offset));}
   assert.equal(actual.toString('hex'),want,`${f.name} group ${i} shot ${j}`);++shots;
  });
 });
 for(const size of [0,4,0xdf,0x108,b.length-5]){assert.equal(c.open_sht(p,size),0,`${f.name} truncated ${size}`);++negative;}
 for(const [at,value] of [[0,0],[2,0xffff],[0xe0,0xfffffff0]]){
  new Uint8Array(c.memory.buffer,p,b.length).set(b);const view=new DataView(c.memory.buffer);if(at<4)view.setUint16(p+at,value,true);else view.setUint32(p+at,value,true);
  assert.equal(c.open_sht(p,b.length),0);++negative;
 }
 c.release(p);
}
assert.equal(c.voice_count(),audio.voices.length);assert.equal(c.sample_count(),audio.samples.length);
audio.voices.forEach(v=>assert.deepEqual([0,1,2].map(f=>c.voice_value(v.id,f)),[v.sample,v.volume,v.metadata]));
audio.samples.forEach((s,i)=>{const p=c.sample_name(i),memory=new Uint8Array(c.memory.buffer);assert.equal(new TextDecoder().decode(memory.subarray(p,memory.indexOf(0,p))),s.name);});
const report={passed:true,nativeExecutableSha256:proof.executableSha256,files:proof.files.map(f=>({name:f.name,sha256:f.sha256})),groups,shots,negative,samples:audio.samples.length,voices:audio.voices.length,
 scope:'All six native SHT loader outputs, preserving new header/shot fields and resolving callback selectors through the retail lookup tables for comparison. Actual shot callbacks/gameplay and audio scheduling remain separate work.',wasmSha256:sha(bytes),
 sourceHashes:Object.fromEntries([...sources,'cpp/game/ShtResource.hpp','cpp/game/SoundEffects.hpp','cpp/game/Th14AudioTables.inc'].map(p=>[p,sha(readFileSync(resolve(rt,p)))])),toolHashes:Object.fromEntries(['tools/th14-sht-native.py','tools/th14-resources-check.mjs'].map(p=>[p,sha(readFileSync(resolve(root,p)))]))};
writeFileSync(resolve(root,'docs/porting/th14-resources-verified.json'),JSON.stringify(report,null,2)+'\n');
console.log(`PASS: 6 SHT files, ${groups} groups, ${shots} native shot records, ${negative} malformed inputs; 65 samples / 76 voices.`);
