import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web');
const out=resolve(root,'artifacts/th14/physical-texture32-post-reset/precision-diagnostic');mkdirSync(out,{recursive:true});
const sha=b=>createHash('sha256').update(b).digest('hex');
const objects=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-text-check/objects.json')));
for(const [p,h] of Object.entries(objects.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h);
const source=readFileSync(resolve(rt,'cpp/game/ImageResample.cpp'),'utf8');
const native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/physical-texture32-post-reset/64/native.json')));
const binary=readFileSync(resolve(root,'artifacts/th14/physical-texture32-post-reset/64/textures.bin'));assert.equal(sha(binary),native.binarySha256);
const tables=JSON.parse(readFileSync(resolve(root,'artifacts/th14/physical-texture32-post-reset/weights32-native.json'))).tables;
const archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json')));
const compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const rest=Object.keys(objects.objectHashes).filter(p=>!p.endsWith('cpp_game_ImageResample.cpp.o'));
const results=[];
const variants=process.argv[2]?process.argv[2].split(',').map(Number):[0,1,2,3,4,5,6,7];
function replace(s,from,to){assert.equal(s.split(from).length,2,from);return s.replace(from,to);}
for(const variant of variants){
 let s=source;
 if(variant&1){
  s=replace(s,'if(mirror){weight=float(float(end+start)*half_step)-origin;','if(mirror){weight=float((double(end)+start)*half_step-origin);');
  s=replace(s,'if(mirror)accumulated=float(end-start)*weight+accumulated;else','if(mirror)accumulated=float((double(end)-start)*weight+accumulated);else');
 }
 if(variant&2)s=replace(s,'if(mirror)p[c]=weight*rgba[c]+p[c];else','if(mirror)p[c]=float(double(weight)*rgba[c]+p[c]);else');
 if(variant&4)s=replace(s,'u32(truncate_positive(double(truncate_positive(double(v)*mask))+.5))','(mirror?u32(double(v)*mask+.5):u32(truncate_positive(double(truncate_positive(double(v)*mask))+.5)))');
 if(variant&8){
  s=replace(s,'if(half)weight=1.f-weight;','const double effective_weight=half?1.-double(weight):double(weight);if(half)weight=1.f-weight;');
  s=replace(s,'if(mirror)accumulated=float((double(end)-start)*weight+accumulated);else','if(mirror)accumulated=float((double(end)-start)*effective_weight+accumulated);else');
 }
 s+=`\nnamespace th11 {static std::vector<Weight> diagnostic;extern "C" __attribute__((export_name("diagnostic_weights"))) u32 diagnostic_weights(u32 s,u32 d){diagnostic.clear();for(const auto& row:weights(s,d,true)){diagnostic.push_back({u32(row.size()),0});diagnostic.insert(diagnostic.end(),row.begin(),row.end());}return diagnostic.size();}extern "C" __attribute__((export_name("diagnostic_data"))) const void* diagnostic_data(){return diagnostic.data();}}\n`;
 const cpp=resolve(out,`variant${variant}.cpp`),obj=resolve(out,`variant${variant}.o`),wasm=resolve(out,`variant${variant}.wasm`);writeFileSync(cpp,s);
 const flags=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14'];
 const options={cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true};
 execFileSync(compiler,[...flags,'-Icpp/game','-c',cpp,'-o',obj],options);
 execFileSync(compiler,[...flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','tests/cpp/th14-physical-texture-image-fixture.cpp',...rest,obj,'-o',wasm],options);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(readFileSync(wasm),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;
 const differences=[];let name='',differentBytes=0;
 for(const n of native.cases){
  if(name!==n.name){name=n.name;const raw=readFileSync(resolve(archive.extraction,name)),p=c.allocate(raw.length);new Uint8Array(c.memory.buffer,p,raw.length).set(raw);assert.equal(c.open(p,raw.length),1);c.release(p);}
  assert.equal(c.load(n.chunk),1);assert.equal(c.size(),n.bytes);
  const actual=Buffer.from(new Uint8Array(c.memory.buffer,c.data(),c.size())),expected=binary.subarray(n.offset,n.offset+n.bytes);let count=0;const first=[];
  for(let i=0;i<n.bytes;i++)if(actual[i]!==expected[i]){count++;if(first.length<8)first.push([i,actual[i],expected[i]]);}
  if(count)differences.push({name:n.name,chunk:n.chunk,differentBytes:count,first});differentBytes+=count;
 }
 const weightDifferences=[];
 for(const t of tables){
  const count=c.diagnostic_weights(t.source,t.destination),words=new Uint32Array(c.memory.buffer,c.diagnostic_data(),count*2);let at=0;
  for(let i=0;i<t.source;i++){
   const n=words[at];at+=2;const row=[];for(let j=0;j<n;j++){row.push([words[at],words[at+1]]);at+=2;}
   if(JSON.stringify(row)!==JSON.stringify(t.weights[i]))weightDifferences.push({source:t.source,destination:t.destination,sample:i,actual:row,expected:t.weights[i]});
  }
  assert.equal(at,words.length);
 }
 const result={diagnosticOnly:true,variant,cases:differences.length,differentBytes,weightDifferences:weightDifferences.length,differences,weightDetails:weightDifferences,sourceSha256:sha(Buffer.from(s)),wasmSha256:sha(readFileSync(wasm)),nativePixelsSha256:native.binarySha256};
 results.push(result);writeFileSync(resolve(out,`variant${variant}.json`),JSON.stringify(result,null,2)+'\n');
 console.log(JSON.stringify({variant,cases:result.cases,differentBytes,weightDifferences:weightDifferences.length,first:differences.slice(0,1)}));
}
writeFileSync(resolve(out,'results.json'),JSON.stringify(results,null,2)+'\n');
