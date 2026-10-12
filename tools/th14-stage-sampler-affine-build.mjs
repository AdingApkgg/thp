// Diagnostic interpolation reassociation; normalization changes homogeneous
// clipping and is not a production fix or a full-scene equivalence claim.
import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
for(const [name,parent] of [['sampler-uv-affine-gpu','sampler-uv-viewport-mad'],['sampler-uv-affine-cpu','sampler-uv-viewport-fma']]){
 const source=resolve(base,'variants',parent),before=JSON.parse(readFileSync(resolve(source,'build.json'))),out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp','fixture.cpp'];
 for(const file of files){let s=readFileSync(resolve(source,file),'utf8');if(file==='Shaders.hpp'){
 assert(s.includes('out vec2 vUV;'));s=s.replace('out vec2 vUV;','out vec2 vUV;out float vInverseW;');
 const anchor='float z=rangeFog?length(eye.xyz):abs(eye.z);';assert(s.includes(anchor));s=s.replace(anchor,'vInverseW=1.0/gl_Position.w;vUV*=vInverseW;gl_Position.xyz*=vInverseW;gl_Position.w=1.0;'+anchor);
 assert(s.includes('in vec2 vUV;'));s=s.replace('in vec2 vUV;','in vec2 vUV;in float vInverseW;');
 assert(s.includes('texture(tex,vUV)'));s=s.replace('texture(tex,vUV)','texture(tex,vUV/vInverseW)');assert(s.includes('outColor=vec4(vUV,0.0,1.0);'));s=s.replace('outColor=vec4(vUV,0.0,1.0);','outColor=vec4(vUV/vInverseW,0.0,1.0);');
 }writeFileSync(resolve(out,file),s);}
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,parent,baseBuildSha256:sha(readFileSync(resolve(source,'build.json'))),sources:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built affine varying diagnostic',name);
}
