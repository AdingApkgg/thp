// Isolate viewport quantization before the GLES half-pixel conversion.
import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),source=resolve(base,'variants/world-uv-cpu-clip'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex'),before=JSON.parse(readFileSync(resolve(source,'build.json')));
for(const mode of ['gpu-snap8','cpu-snap8']){
 const name='world-uv-viewport-'+mode,out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp','fixture.cpp'];
 for(const file of files){let s=readFileSync(resolve(source,file),'utf8');
  if(file==='Shaders.hpp'){
   const anchor='gl_Position.xy+=gl_Position.w/viewport.zw;';assert(s.includes(anchor));
   if(mode==='gpu-snap8')s=s.replace(anchor,'vec2 screen=(gl_Position.xy/gl_Position.w*0.5+vec2(0.5))*viewport.zw;screen=roundEven(screen*256.0)/256.0;gl_Position.xy=((screen+vec2(0.5))/viewport.zw*2.0-vec2(1.0))*gl_Position.w;');
   else {s=s.replace('layout(location=8) in vec4 instanceFactor;','layout(location=8) in vec4 instanceFactor;\nlayout(location=9) in vec3 viewportSnap;');s=s.replace(anchor,'if(viewportSnap.z!=0.0)gl_Position.xy=((viewportSnap.xy+vec2(0.5))/viewport.zw*2.0-vec2(1.0))*gl_Position.w;else '+anchor);}
  }
  if(mode==='cpu-snap8'&&file==='Renderer.cpp'){
   const anchor=' const u32 base=upload(vertices,GL_ARRAY_BUFFER,data,size,1048576);';assert(s.includes(anchor));
   s=s.replace(anchor,` const u32 inputStride=d.stride+12;std::vector<u8> expanded;expanded.resize((size/d.stride)*inputStride);
 auto viewportMultiply=[](const std::array<float,16>& A,const std::array<float,16>& B){std::array<float,16>C{};for(int col=0;col<4;col++)for(int row=0;row<4;row++){float sum=A[row]*B[col*4];for(int k=1;k<4;k++)sum+=A[k*4+row]*B[col*4+k];C[col*4+row]=sum;}return C;};const auto clip=viewportMultiply(d.matrix[2],viewportMultiply(d.matrix[1],d.matrix[0]));
 for(u32 i=0;i<size/d.stride;i++){auto dst=expanded.data()+i*inputStride;auto src=static_cast<const u8*>(data)+i*d.stride;std::memcpy(dst,src,d.stride);float v[4]{0,0,0,1},q[4]{},snap[3]{};std::memcpy(v,src,12);for(int row=0;row<4;row++){q[row]=clip[row]*v[0];for(int k=1;k<4;k++)q[row]+=clip[k*4+row]*v[k];}if(!transformed&&std::isfinite(q[3])&&q[3]!=0){double x=(double(q[0])/q[3]*0.5+0.5)*d.viewport.width,y=(-double(q[1])/q[3]*0.5+0.5)*d.viewport.height;if(std::isfinite(x)&&std::isfinite(y)){snap[0]=float(std::nearbyint(x*256)/256);snap[1]=float(std::nearbyint(y*256)/256);snap[2]=1;}}std::memcpy(dst+d.stride,snap,12);}
 const u32 base=upload(vertices,GL_ARRAY_BUFFER,expanded.data(),expanded.size(),1048576);`);
   const begin=s.indexOf('glEnableVertexAttribArray(0);glVertexAttribPointer(0,'),end=s.indexOf('\n }\n constexpr GLenum modes',begin);assert(begin>=0&&end>begin);let section=s.slice(begin,end).replaceAll('d.stride','inputStride');section+='\n glEnableVertexAttribArray(9);glVertexAttribPointer(9,3,GL_FLOAT,false,inputStride,reinterpret_cast<void*>(base+d.stride));';s=s.slice(0,begin)+section+s.slice(end);
  }writeFileSync(resolve(out,file),s);
 }
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(source,'build.json'))),sources:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built isolated viewport quantization',mode);
}
