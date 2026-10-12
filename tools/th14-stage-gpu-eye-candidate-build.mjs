// Source-bound CPU world/view association candidates, isolated from production.
import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),source=resolve(base,'variants/cpu-clip-depth-fixed20'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex'),before=JSON.parse(readFileSync(resolve(source,'build.json')));
for(const name of ['cpu-clip-eye-depth-fixed20','cpu-clip-eye-dot-depth-fixed20','cpu-clip-eye-pair-depth-fixed20']){
 const out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp','fixture.cpp'];
 for(const file of files){let s=readFileSync(resolve(source,file),'utf8');
  if(file==='Renderer.cpp'){
   assert(s.includes('"clipMatrix"'));s=s.replace('"clipMatrix"','"clipMatrix","eyeMatrix"');assert(s.includes('i<27;i++'));s=s.replace('i<27;i++','i<28;i++');
   const anchor='auto combined=multiply(d.matrix[2],multiply(d.matrix[1],d.matrix[0]));uniform(26,16,combined.data());';assert(s.includes(anchor));s=s.replace(anchor,'auto eye=multiply(d.matrix[1],d.matrix[0]);auto combined=multiply(d.matrix[2],eye);uniform(26,16,combined.data());uniform(27,16,eye.data());');
  }
  if(file==='Shaders.hpp'){
   assert(s.includes('textureMatrix,clipMatrix;'));s=s.replace('textureMatrix,clipMatrix;','textureMatrix,clipMatrix,eyeMatrix;');const anchor='vec4 eye=view*model*vec4(position.xyz,1.0);';assert(s.includes(anchor));
   if(name==='cpu-clip-eye-depth-fixed20')s=s.replace(anchor,'vec4 eye=eyeMatrix*vec4(position.xyz,1.0);');
   else {
    s=s.replace('uniform bool instanced;','uniform bool instanced;\nuniform highp uint eyeRoundingFence;');s=s.replace('void main(){','vec4 eyeFence(vec4 v){return uintBitsToFloat(floatBitsToUint(v)^uvec4(eyeRoundingFence));}\nvoid main(){');
    const expression=name==='cpu-clip-eye-pair-depth-fixed20'?'eyeFence(eyeFence(e0+e1)+eyeFence(e2+e3))':'eyeFence(eyeFence(eyeFence(e0+e1)+e2)+e3)';s=s.replace(anchor,'vec4 e0=eyeFence(eyeMatrix[0]*position.x),e1=eyeFence(eyeMatrix[1]*position.y),e2=eyeFence(eyeMatrix[2]*position.z),e3=eyeMatrix[3];vec4 eye='+expression+';');
   }
  }writeFileSync(resolve(out,file),s);
 }
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(source,'build.json'))),sources:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built isolated eye association',name);
}
