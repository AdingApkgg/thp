import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {WASI} from 'node:wasi';
import {fullApplicationGlesPlatform} from './th14-full-application-gles-transition-type0-nov09.mjs';
const R=resolve(import.meta.dirname,'..'),H=resolve(R,'artifacts/th14/ascii-atlas-raster-nov12'),O=resolve(H,'gles');mkdirSync(O);
const read=p=>readFileSync(p),sha=b=>createHash('sha256').update(b).digest('hex'),load=p=>JSON.parse(read(p));
const build=load(resolve(H,'component/build.json')),wasm=read(resolve(H,'component/probe.wasm'));
assert.equal(sha(wasm),build.wasmSha256);assert.equal(sha(read(resolve(R,'tools/th14-ascii-atlas-raster-component-nov12.cpp'))),build.fixtureSha256);
for(const [p,d]of Object.entries({...build.sourceBindings,...build.objectBindings}))assert.equal(sha(read(resolve(R,p))),d,p);
const ref=load(resolve(H,'d3d9/report.json')),native=read(resolve(H,'d3d9/native.bgra')),geometry=load(resolve(H,'geometry/report.json'));
assert.equal(sha(native),ref.rawSha256);assert.equal(ref.cases.length,18);assert.equal(sha(read(resolve(H,'geometry/report.json'))),ref.originalGeometryReportSha256);
const archive=load(resolve(R,'artifacts/archive-differential/th14.json')),asset=read(resolve(archive.extraction,'ascii.anm'));assert.equal(sha(asset),ref.assetSha256);
const module=new WebAssembly.Module(wasm),memory=new WebAssembly.Memory({initial:1024,maximum:16384,shared:true});
const platform=fullApplicationGlesPlatform(module,memory,{clockInput:0,archivePath:'',fontDirectory:'',saveDirectory:O,angleDirectory:'C:/Users/APKGG/AppData/Local/Programs/Trae'});
const wasi=new WASI({version:'preview1',args:[],env:{},preopens:{},returnOnExit:true});
let c,created=false,exception=null,closed=false;const rows=[];let differentPixels=0,differentChannels=0,maxDelta=0;
const began=performance.now();
try{
 const instance=new WebAssembly.Instance(module,{env:platform.env,wasi_snapshot_preview1:wasi.wasiImport});c=instance.exports;platform.attach(c);wasi.initialize(instance);
 const p=c.allocate(asset.length);new Uint8Array(memory.buffer,p,asset.length).set(asset);created=true;assert.equal(c.setup(p,asset.length),1);c.release(p);
 for(const [index,row]of ref.cases.entries()){
  assert.equal(c.run(row.width,row.height,row.font,row.passIndex),1);assert.equal(platform.getError(),0);
  const cpp=Buffer.from(memory.buffer,c.pixels(),c.pixel_bytes()),original=native.subarray(row.offset,row.offset+row.bytes);assert.equal(cpp.length,row.bytes);
  let pixels=0,channels=0,alpha=0,delta=0;const first=[];
  for(let i=0;i<cpp.length;i+=4){let mismatch=false;for(let k=0;k<4;k++){const d=Math.abs(cpp[i+k]-original[i+k]);if(d){channels++;if(k===3)alpha++;mismatch=true;delta=Math.max(delta,d);}}
   if(mismatch){pixels++;if(first.length<12)first.push({x:(i/4)%row.width,y:Math.floor(i/4/row.width),native:Array.from(original.subarray(i,i+4)),cpp:Array.from(cpp.subarray(i,i+4))});}}
  const nonBackground=original.reduce((n,_,i)=>i%4===0&&original.readUInt32LE(i)!==0x7f42678b?n+1:n,0);
  rows.push({...row,cppSha256:sha(cpp),differentPixels:pixels,differentChannels:channels,differentAlphaBytes:alpha,maxDelta:delta,originalNonBackgroundPixels:nonBackground,firstDifferences:first});
  differentPixels+=pixels;differentChannels+=channels;maxDelta=Math.max(maxDelta,delta);
  if(pixels&&rows.filter(r=>r.differentPixels).length<=2){writeFileSync(resolve(O,`failed-${index}-cpp.bgra`),cpp);writeFileSync(resolve(O,`failed-${index}-native.bgra`),original);}
 }
}catch(e){exception=String(e?.stack??e);}
finally{
 if(created)try{c.close();closed=true;}catch(e){exception??=String(e?.stack??e);}
 try{platform.closeGpu();}catch(e){exception??=String(e?.stack??e);}
}
const report={cases:rows.length,rows,differentPixels,differentChannels,maxDelta,exception,closed,gpuContextClosed:platform.context.closed,
 gpu:platform.gpu.summary(),platform:platform.summary(),elapsedSeconds:(performance.now()-began)/1000,
 wasmSha256:sha(wasm),checkerSha256:sha(read(import.meta.filename)),declaredFogAndDepthDisabled:true,actualCurrentCppResourceTextAndRenderer:true,
 originalGeometryButSeparateD3d9Device:true,newOriginalGameRuns:0,audibleOutput:false,browserUiAcceptance:false,completeGame:false};
writeFileSync(resolve(O,'report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({cases:rows.length,differentPixels,differentChannels,maxDelta,exception,closed,gpuContextClosed:report.gpuContextClosed,seconds:report.elapsedSeconds,first:rows.filter(r=>r.differentPixels).slice(0,2)}));
assert.equal(exception,null);assert.equal(rows.length,18);assert(closed&&report.gpuContextClosed);assert.equal(report.platform.audioBytes,0);
assert(Object.values(report.gpu.liveObjects).every(n=>n===0));assert.equal(differentPixels,0);
