// Separate remaining color arithmetic from already scoped geometry/depth changes.
import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),source=resolve(base,'variants/cpu-eye-viewport-depth-fixed20'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex'),before=JSON.parse(readFileSync(resolve(source,'build.json')));
for(const name of ['viewport-no-fog','viewport-fog-product-sum','viewport-fog-product-subtract']){
 const out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp','fixture.cpp'];
 for(const file of files){let s=readFileSync(resolve(source,file),'utf8');
  if(name==='viewport-no-fog'&&file==='fixture.cpp'){const anchor='renderer->draw(Topology::Strip,count,words,stride);renderer->flush();return 1;';assert(s.includes(anchor));s=s.replace(anchor,'renderer->pipeline().fog=false;'+anchor);}
  if(name!=='viewport-no-fog'&&file==='Shaders.hpp'){
   const anchor='mix(fogColor.rgb,c.rgb,clamp(vFog,0.0,1.0))';assert(s.includes(anchor));
   s=s.replace(anchor,name==='viewport-fog-product-sum'?'c.rgb*clamp(vFog,0.0,1.0)+fogColor.rgb*(1.0-clamp(vFog,0.0,1.0))':'c.rgb*clamp(vFog,0.0,1.0)+fogColor.rgb-fogColor.rgb*clamp(vFog,0.0,1.0)');
  }writeFileSync(resolve(out,file),s);
 }
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(source,'build.json'))),sources:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built scoped fog/color isolation',name);
}
