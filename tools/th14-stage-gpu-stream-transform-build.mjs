// Mathematical-order hypotheses in isolated fixture/source copies only.
import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const before=JSON.parse(readFileSync(resolve(base,'build.json'))),original='runtimes/th12/th12_web/tests/cpp/th14-stage-gpu-stream-fixture.cpp';
for(const name of ['sequential-eye','cpu-float-eye','cpu-double-eye','no-fog','no-depth']){
 const out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp'];
 for(const file of files){let source=readFileSync(resolve(root,'runtimes/th12/portable/sdl',file),'utf8');
  if(file==='Shaders.hpp'&&name==='sequential-eye'){const anchor='vec4 eye=view*model*vec4(position.xyz,1.0);';assert(source.includes(anchor));source=source.replace(anchor,'vec4 eye=view*(model*vec4(position.xyz,1.0));');}
  writeFileSync(resolve(out,file),source);
 }
 let fixture=readFileSync(resolve(root,original),'utf8').replace('../../../portable/sdl/Renderer.hpp','Renderer.hpp');
 if(name.startsWith('cpu-')){
  const anchor='renderer->draw(Topology::Strip,count,words,stride);return 1;',type=name==='cpu-float-eye'?'float':'double';assert(fixture.includes(anchor));
  fixture=fixture.replace(anchor,'auto world=renderer->state.matrix[0],view=renderer->state.matrix[1];std::array<float,16> combined{};for(u32 col=0;col<4;col++)for(u32 row=0;row<4;row++){'+type+' sum='+type+'(view[row])*'+type+'(world[col*4]);for(u32 k=1;k<4;k++)sum+='+type+'(view[k*4+row])*'+type+'(world[col*4+k]);combined[col*4+row]=float(sum);}renderer->state.matrix[0]=combined;renderer->state.matrix[1]={1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1};renderer->draw(Topology::Strip,count,words,stride);renderer->flush();renderer->state.matrix[0]=world;renderer->state.matrix[1]=view;return 1;');
 }
 if(name==='no-fog'||name==='no-depth'){
  const anchor='renderer->draw(Topology::Strip,count,words,stride);return 1;';assert(fixture.includes(anchor));
  const change=name==='no-fog'?'renderer->state.pipeline.fog=false;':'renderer->state.pipeline.depthTest=false;renderer->state.pipeline.depthWrite=false;';
  fixture=fixture.replace(anchor,'auto saved=renderer->state.pipeline;'+change+'renderer->draw(Topology::Strip,count,words,stride);renderer->flush();renderer->state.pipeline=saved;return 1;');
 }
 writeFileSync(resolve(out,'fixture.cpp'),fixture);
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(base,'build.json'))),sources:Object.fromEntries([...files,'fixture.cpp'].map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built isolated Stage matrix hypothesis',name);
}
