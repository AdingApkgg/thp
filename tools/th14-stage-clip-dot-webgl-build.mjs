import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),source=resolve(base,'variants/world-uv-cpu-clip'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex'),before=JSON.parse(readFileSync(resolve(source,'build.json')));
for(const mode of ['matrix','mov-control']){
 const name='clip-dot-webgl-'+mode,out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp','fixture.cpp'];
 for(const file of files){let s=readFileSync(resolve(source,file),'utf8');if(file==='Shaders.hpp'){
  s=s.replace('out vec4 vColor,vSpecular;','out vec4 vColor,vSpecular,vClip;').replace('in vec4 vColor,vSpecular;','in vec4 vColor,vSpecular,vClip;');
  const anchor='gl_Position=clipMatrix*vec4(position.xyz,1.0);';assert(s.includes(anchor));s=s.replace(anchor,anchor+(mode==='matrix'?'vClip=gl_Position;':'vClip=vec4(position.xyz,1.0);'));
  const tail='vFog=fogEnabled?(transformed?specular.a:fog):1.0;';assert(s.includes(tail));s=s.replace(tail,tail+'gl_Position=vec4((gl_VertexID&1)!=0?0.5:-0.5,(gl_VertexID&2)!=0?0.5:-0.5,0.5,1.0);');
  assert(s.includes('outColor=vec4(vUV,0.0,1.0);'));s=s.replace('outColor=vec4(vUV,0.0,1.0);','outColor=vClip;');
 }writeFileSync(resolve(out,file),s);}
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(source,'build.json'))),sources:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built isolated vertex arithmetic readback',mode);
}
