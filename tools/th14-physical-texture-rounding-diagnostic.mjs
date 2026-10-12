import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/physical-texture32-pixels/rounding-diagnostic');mkdirSync(out,{recursive:true});
const objects=JSON.parse(readFileSync(resolve(root,'artifacts/th14/dialogue-text-check/objects.json'))),source=readFileSync(resolve(rt,'cpp/game/ImageResample.cpp'),'utf8'),native=JSON.parse(readFileSync(resolve(root,'artifacts/th14/physical-texture32-pixels/53/native.json'))),binary=readFileSync(resolve(root,'artifacts/th14/physical-texture32-pixels/53/textures.bin')),archive=JSON.parse(readFileSync(resolve(root,'artifacts/archive-differential/th14.json')));
const compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),rest=Object.keys(objects.objectHashes).filter(n=>!n.endsWith('cpp_game_ImageResample.cpp.o')),results=[];
const selection=process.argv[2]?process.argv[2].split(',').map(Number):Array.from({length:8},(_,i)=>i);
for(const variant of selection){
 let text=source;
 if(variant<8&&variant&1)text=text.replace('levels[c][n]=float(n)*unit','levels[c][n]=mirror?float(double(n)/mask):float(n)*unit');
 if(variant<8&&variant&2)text=text.replace('u32(truncate_positive(double(truncate_positive(double(v)*mask))+.5))','mirror?u32(float(double(v)*mask+.5)):u32(truncate_positive(double(truncate_positive(double(v)*mask))+.5))');
 if((variant<8&&variant&4)||variant>=8)text=text.replace('p[c]=float(double(weight)*rgba[c]+p[c])','p[c]=mirror?float(float(weight*rgba[c])+p[c]):float(double(weight)*rgba[c]+p[c])');
 if(variant>=10)text=text.replace('float weight=float((double(end)+start)*half_step-origin);if(half)weight=1.f-weight;accumulated=float((double(end)-start)*weight+accumulated);','float weight=mirror?float(float(float(end+start)*half_step)-origin):float((double(end)+start)*half_step-origin);if(half)weight=1.f-weight;accumulated=mirror?float(float(float(end-start)*weight)+accumulated):float((double(end)-start)*weight+accumulated);');
 if(variant>=11)text=text.replace('upper=scale+lower;', 'upper=scale+lower;const float clipped_lower=mirror?std::max(lower,0.f):lower,clipped_upper=mirror?std::min(upper,float(destination)):upper;').replace('std::floor(lower));float(pixel)<upper','std::floor(clipped_lower));float(pixel)<clipped_upper').replace('std::max(start,lower);end=std::min(end,upper)','std::max(start,clipped_lower);end=std::min(end,clipped_upper)').replace('if(half)weight=1.f-weight;', 'if(mirror){if(origin<0)weight=1;else if(float(origin+1.f)>=float(source))weight=0;}if(half)weight=1.f-weight;');
 if(variant>=8)text=text.replace('u32(truncate_positive(double(truncate_positive(double(v)*mask))+.5))',variant===8?'(mirror&&oc.bytes==4)?u32(float(float(v*float(mask))+.5f)):u32(truncate_positive(double(truncate_positive(double(v)*mask))+.5))':variant===9?'(mirror&&oc.bytes==4)?u32(truncate_positive(double(v)*mask+.5)):u32(truncate_positive(double(truncate_positive(double(v)*mask))+.5))':'u32(truncate_positive(double(truncate_positive(double(v)*mask))+.5))');
 text+=`
namespace th11 { static std::vector<Weight> diagnostic; extern "C" __attribute__((export_name("diagnostic_weights"))) u32 diagnostic_weights(u32 s,u32 d){diagnostic.clear(); for(const auto& row:weights(s,d,true)){ diagnostic.push_back({u32(row.size()),0}); diagnostic.insert(diagnostic.end(),row.begin(),row.end()); }return diagnostic.size();} extern "C" __attribute__((export_name("diagnostic_data"))) const void* diagnostic_data(){return diagnostic.data();} }
`;
 const cpp=resolve(out,`variant${variant}.cpp`),obj=resolve(out,`variant${variant}.o`),wasm=resolve(out,`variant${variant}.wasm`);writeFileSync(cpp,text);
 const flags=['--target=wasm32-wasip1','-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14'];
 const options={cwd:rt,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true};
 execFileSync(compiler,[...flags,'-Icpp/game','-c',cpp,'-o',obj],options);
 execFileSync(compiler,[...flags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','tests/cpp/th14-physical-texture-image-fixture.cpp',...rest,obj,'-o',wasm],options);
 const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{}}),{instance}=await WebAssembly.instantiate(readFileSync(wasm),{wasi_snapshot_preview1:wasi.wasiImport});wasi.initialize(instance);const c=instance.exports;let name='',differentBytes=0;const differences=[];
 for(const n of native.cases){
  if(name!==n.name){name=n.name;const raw=readFileSync(resolve(archive.extraction,name)),p=c.allocate(raw.length);new Uint8Array(c.memory.buffer,p,raw.length).set(raw);assert.equal(c.open(p,raw.length),1);c.release(p);}
  assert.equal(c.load(n.chunk),1);assert.equal(c.size(),n.bytes);const actual=Buffer.from(new Uint8Array(c.memory.buffer,c.data(),c.size())),expected=binary.subarray(n.offset,n.offset+n.bytes);let count=0;const first=[];
  for(let i=0;i<n.bytes;++i)if(actual[i]!==expected[i]){++count;if(first.length<8)first.push([i,actual[i],expected[i]]);}
  if(count)differences.push({name:n.name,chunk:n.chunk,differentBytes:count,first});differentBytes+=count;
 }
 const weightDifferences=[];const tables=JSON.parse(readFileSync(resolve(root,'artifacts/th14/physical-texture32-pixels/weights32.json'))).tables;
 for(const t of tables){const count=c.diagnostic_weights(t.source,t.destination),words=new Uint32Array(c.memory.buffer,c.diagnostic_data(),count*2);let at=0;for(let i=0;i<t.source;++i){const n=words[at];at+=2;const row=[];for(let j=0;j<n;++j){const bits=words[at+1],bytes=Buffer.alloc(4);bytes.writeUInt32LE(bits);row.push([words[at],bytes.readFloatLE()]);at+=2;}if(JSON.stringify(row)!==JSON.stringify(t.weights[i]))weightDifferences.push({source:t.source,destination:t.destination,sample:i,actual:row,expected:t.weights[i]});}assert.equal(at,words.length);}
 writeFileSync(resolve(out,`weights${variant}.json`),JSON.stringify(weightDifferences,null,2)+'\n');console.log('weight differences',variant,weightDifferences.length,JSON.stringify(weightDifferences.slice(-4)));
 const result={variant,cases:differences.length,differentBytes,differences};results.push(result);writeFileSync(resolve(out,`variant${variant}.json`),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({variant,cases:result.cases,differentBytes,first:differences.slice(0,1)}));
}
writeFileSync(resolve(out,'results.json'),JSON.stringify(results,null,2)+'\n');
