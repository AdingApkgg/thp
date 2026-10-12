import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-world-profiles'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',base=JSON.parse(readFileSync(resolve(out,'correct-separate/build.json'))),fixture='runtimes/th12/th12_web/tests/cpp/th14-gpu-world-profiles-fixture.cpp';
const linear=process.argv.includes('--linear');
for(const name of linear?['linear-scaled','linear-mad','linear-cpu']:['range-rsqrt','range-sqrt']){
 const destination=resolve(out,name);mkdirSync(destination,{recursive:true});
 for(const file of ['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp']){
  let source=readFileSync(resolve(out,'correct-separate',file),'utf8');
  if(file==='Shaders.hpp'){
   const anchor=linear?'(fogParams.y-z)/(fogParams.y-fogParams.x)':'length(eye.xyz)';assert.ok(source.includes(anchor));
   const expression=linear?(name==='linear-scaled'?'(fogParams.y-z)*(1.0/(fogParams.y-fogParams.x))':name==='linear-mad'?'fogParams.y/(fogParams.y-fogParams.x)-z/(fogParams.y-fogParams.x)':'(fogParams.y-z)*fogParams.x'):(name==='range-rsqrt'?'1.0/inversesqrt(dot(eye.xyz,eye.xyz))':'sqrt(dot(eye.xyz,eye.xyz))');source=source.replace(anchor,expression);
  }
  if(name==='linear-cpu'&&file==='Renderer.cpp'){
   const anchor='?2.71828f:p.fogNear';assert.ok(source.includes(anchor));source=source.replace(anchor,'?2.71828f:1.0f/(p.fogFar-p.fogNear)');
  }
  writeFileSync(resolve(destination,file),source);
 }
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...base.flags,fixture,resolve(destination,'Renderer.cpp'),'-o',resolve(destination,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:destination,TMP:destination,TMPDIR:destination},stdio:'inherit',windowsHide:true});
 const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'];
 writeFileSync(resolve(destination,'build.json'),JSON.stringify({...base,name,sources:Object.fromEntries(files.map(f=>[f,sha(readFileSync(resolve(destination,f)))])),wasmSha256:sha(readFileSync(resolve(destination,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(destination,'gpu.mjs')))},null,2)+'\n');console.log('Built '+name);
}
