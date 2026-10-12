// Isolate CPU matrix association and GPU dot-product rounding.
import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),source=resolve(base,'variants/cpu-float-clip'),sha=b=>createHash('sha256').update(b).digest('hex'),before=JSON.parse(readFileSync(resolve(source,'build.json')));
for(const name of ['cpu-viewproj-clip','clip-dot-separate','clip-dot-pair','clip-dot-reverse']){
 const out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp','fixture.cpp'];
 for(const file of files){let s=readFileSync(resolve(source,file),'utf8');
  if(name==='cpu-viewproj-clip'&&file==='Renderer.cpp'){const a='multiply(d.matrix[2],multiply(d.matrix[1],d.matrix[0]))';assert(s.includes(a));s=s.replace(a,'multiply(multiply(d.matrix[2],d.matrix[1]),d.matrix[0])');}
  if(name.startsWith('clip-dot-')&&file==='Shaders.hpp'){
   assert(s.includes('gl_Position=clipMatrix*vec4(position.xyz,1.0);'));
   s=s.replace('uniform mat4 world,view,projection,textureMatrix,clipMatrix;','uniform mat4 world,view,projection,textureMatrix,clipMatrix;\nuniform highp uint clipRoundingFence;');
   const functions='vec4 fence(vec4 v){return uintBitsToFloat(floatBitsToUint(v)^uvec4(clipRoundingFence));}\n';
   s=s.replace('void main(){',functions+'void main(){');
   const expression=name==='clip-dot-pair'?'fence(fence(t0+t1)+fence(t2+t3))':name==='clip-dot-reverse'?'fence(fence(fence(t3+t2)+t1)+t0)':'fence(fence(fence(t0+t1)+t2)+t3)';
   s=s.replace('gl_Position=clipMatrix*vec4(position.xyz,1.0);','vec4 t0=fence(clipMatrix[0]*position.x),t1=fence(clipMatrix[1]*position.y),t2=fence(clipMatrix[2]*position.z),t3=clipMatrix[3];gl_Position='+expression+';');
  }writeFileSync(resolve(out,file),s);
 }
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(source,'build.json'))),sources:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built matrix/dot order hypothesis',name);
}
