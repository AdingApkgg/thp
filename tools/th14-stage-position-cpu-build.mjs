import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
for(const name of ['position-invariant','position-cpu-fused','position-cpu-separated']){
 const source=resolve(base,'variants',name==='position-invariant'?'cpu-clip-depth-fixed20':'viewport-fma-scene'),before=JSON.parse(readFileSync(resolve(source,'build.json'))),out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});
 const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp','fixture.cpp'];
 for(const file of files){let s=readFileSync(resolve(source,file),'utf8');assert.equal(sha(Buffer.from(s)),before.sources[file],file);
  if(name==='position-invariant'&&file==='Shaders.hpp')s=s.replace('precision highp float;','precision highp float;\ninvariant gl_Position;');
  if(name!=='position-invariant'&&file==='Renderer.cpp'){
   assert(s.includes('const u32 inputStride=d.stride+12;'));s=s.replace('const u32 inputStride=d.stride+12;','const u32 inputStride=d.stride+16;');
   const begin=s.indexOf(' for(u32 i=0;i<size/d.stride;i++){auto dst=expanded.data()'),end=s.indexOf('\n const u32 base=upload',begin);assert(begin>=0&&end>begin);
   const half=name==='position-cpu-fused'?'q[0]=std::fma(q[3],1.f/float(d.viewport.width),q[0]);q[1]=std::fma(q[3],1.f/float(d.viewport.height),-q[1]);':'q[0]+=q[3]/float(d.viewport.width);q[1]=-q[1]+q[3]/float(d.viewport.height);';
   s=s.slice(0,begin)+' for(u32 i=0;i<size/d.stride;i++){auto dst=expanded.data()+i*inputStride;auto src=static_cast<const u8*>(data)+i*d.stride;std::memcpy(dst,src,d.stride);float v[4]{0,0,0,1},q[4]{};std::memcpy(v,src,12);for(int row=0;row<4;row++){q[row]=clip[row]*v[0];for(int k=1;k<4;k++)q[row]=std::fma(clip[k*4+row],v[k],q[row]);}if(!transformed){'+half+'}std::memcpy(dst+d.stride,q,16);}'+s.slice(end);
   assert(s.includes('glVertexAttribPointer(9,3,'));s=s.replace('glVertexAttribPointer(9,3,','glVertexAttribPointer(9,4,');
  }
  if(name!=='position-invariant'&&file==='Shaders.hpp'){
   s=s.replace('layout(location=9) in vec3 viewportSnap;','layout(location=9) in vec4 cpuClipPosition;');
   const begin=s.indexOf('  else {gl_Position=clipMatrix*'),end=s.indexOf('\n  vColor=',begin);assert(begin>=0&&end>begin);
   s=s.slice(0,begin)+'  else {gl_Position=cpuClipPosition;gl_Position.z=gl_Position.z*2.0-gl_Position.w;}'+s.slice(end);
  }
  writeFileSync(resolve(out,file),s);
 }
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(source,'build.json'))),sources:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename)),scope:'Isolated vertex arithmetic control; original inputs and D16 candidate retained, no per-pixel fitting or production changes.'},null,2)+'\n');console.log('Built isolated vertex position control',name);
}
