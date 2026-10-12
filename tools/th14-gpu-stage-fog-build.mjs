import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-stage-fog'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',fixture='runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-fog-fixture.cpp';
const flags=JSON.parse(readFileSync(resolve(root,'artifacts/th14/gpu-world/build.json'))).flags.map(f=>f.replace('_gpu_world_case','_gpu_stage_fog_case'));
const extended=process.argv.includes('--range-variants');
for(const [name,source] of process.argv.includes('--rcp-barrier')?[['rcp-barrier','linear-mad']]:process.argv.includes('--rcp-uniform')?[['rcp-uniform','linear-mad']]:extended?[['rsqrt','linear-mad'],['negative','linear-mad'],['cpu','linear-mad']]:[['before','control'],['candidate','linear-mad']]){
 const destination=resolve(out,name),sourceDir=resolve(root,'artifacts/th14/gpu-world-profiles',source);mkdirSync(destination,{recursive:true});
 const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'];for(const file of files){
  let contents=readFileSync(resolve(sourceDir,file),'utf8');
  if(name==='rsqrt'&&file==='Shaders.hpp'){assert.ok(contents.includes('length(eye.xyz)'));contents=contents.replace('length(eye.xyz)','1.0/inversesqrt(dot(eye.xyz,eye.xyz))');}
  if(name==='rcp-uniform'&&file==='Shaders.hpp'){assert.ok(contents.includes('uniform vec3 fogParams;'));contents=contents.replace('uniform vec3 fogParams;','uniform vec4 fogParams;').replace('length(eye.xyz)','fogParams.w/inversesqrt(dot(eye.xyz,eye.xyz))');}
  if(name==='rcp-uniform'&&file==='Renderer.cpp'){const anchor='p.fogFar,p.fogDensity};uniform(11,3,fog)';assert.ok(contents.includes(anchor));contents=contents.replace(anchor,'p.fogFar,p.fogDensity,1.0f};uniform(11,4,fog)');}
  if(name==='rcp-barrier'&&file==='Shaders.hpp'){assert.ok(contents.includes('uniform vec3 fogParams;'));contents=contents.replace('uniform vec3 fogParams;','uniform vec4 fogParams;').replace('length(eye.xyz)','1.0/uintBitsToFloat(floatBitsToUint(inversesqrt(dot(eye.xyz,eye.xyz)))^uint(fogParams.w))');}
  if(name==='rcp-barrier'&&file==='Renderer.cpp'){const anchor='p.fogFar,p.fogDensity};uniform(11,3,fog)';assert.ok(contents.includes(anchor));contents=contents.replace(anchor,'p.fogFar,p.fogDensity,0.0f};uniform(11,4,fog)');}
  if(name==='negative'&&file==='Shaders.hpp'){const anchor='fogParams.y/(fogParams.y-fogParams.x)-z/(fogParams.y-fogParams.x)';assert.ok(contents.includes(anchor));contents=contents.replace(anchor,'z/(fogParams.x-fogParams.y)-fogParams.y/(fogParams.x-fogParams.y)');}
  if(name==='cpu'&&file==='Shaders.hpp'){const anchor='fogParams.y/(fogParams.y-fogParams.x)-z/(fogParams.y-fogParams.x)';assert.ok(contents.includes(anchor));contents=contents.replace(anchor,'fogParams.y*fogParams.x-z*fogParams.x');}
  if(name==='cpu'&&file==='Renderer.cpp'){const anchor='?2.71828f:p.fogNear';assert.ok(contents.includes(anchor));contents=contents.replace(anchor,'?2.71828f:1.0f/(p.fogFar-p.fogNear)');}
  writeFileSync(resolve(destination,file),contents);
 }
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,fixture,resolve(destination,'Renderer.cpp'),'-o',resolve(destination,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:destination,TMP:destination,TMPDIR:destination},stdio:'inherit',windowsHide:true});
 const native=readFileSync(resolve(out,'native.json')),profiles=readFileSync(resolve(out,'profiles.json'));assert.equal(JSON.parse(native).profilesSha256,sha(profiles));
 writeFileSync(resolve(destination,'build.json'),JSON.stringify({diagnosticOnly:true,name,base:source,sources:Object.fromEntries(files.map(f=>[f,sha(readFileSync(resolve(destination,f)))])),fixtureSha256:sha(readFileSync(resolve(root,fixture))),wasmSha256:sha(readFileSync(resolve(destination,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(destination,'gpu.mjs'))),nativeSha256:sha(native),profilesSha256:sha(profiles),flags},null,2)+'\n');console.log('Built stage fog '+name);
}
