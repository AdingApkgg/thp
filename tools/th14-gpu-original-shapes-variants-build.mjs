import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-original-shapes'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';
const base=JSON.parse(readFileSync(resolve(out,'build.json'))),flags=base.flags;
const sources=Object.keys(base.sources).filter(p=>p.endsWith('.cpp')&&!p.endsWith('th14-render-fixture.cpp')&&!p.endsWith('portable/sdl/Renderer.cpp'));
const names=process.argv.slice(2).length?process.argv.slice(2):['clip-linear','clip-mul','color-rcp','clip-color'];
for(const name of names){
 assert.ok(['clip-linear','clip-mul','color-rcp','clip-color','screen-snap','screen-snap-up','strip-direct'].includes(name));
 const dest=resolve(out,name);mkdirSync(dest,{recursive:true});
 const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'];
 for(const file of files){
  let s=readFileSync(resolve(root,'runtimes/th12/portable/sdl',file),'utf8');
  if(file==='Renderer.cpp'&&name==='strip-direct'){
   const old='if(index||primitive<Topology::Triangles||primitive>Topology::Fan)';assert.ok(s.includes(old));
   s=s.replace(old,'if(index||primitive<Topology::Triangles||primitive>Topology::Fan||(state.layout.screen&&primitive==Topology::Strip))');
  }
  if(file==='Shaders.hpp'){
   const old='vec2 xy=(position.xy-viewport.xy+vec2(.5))/viewport.zw;gl_Position=vec4(xy.x*2.0-1.0,xy.y*2.0-1.0,position.z*2.0-1.0,1.0)/position.w;';assert.equal(s.split(old).length,2);
   if(name==='clip-linear'||name==='clip-color')s=s.replace(old,'vec2 xy=(position.xy-viewport.xy)*(vec2(2.0)/viewport.zw)+(vec2(1.0)/viewport.zw-vec2(1.0));gl_Position=vec4(xy,position.z*2.0-1.0,1.0)/position.w;');
   if(name==='clip-mul')s=s.replace(old,'vec2 xy=(position.xy-viewport.xy+vec2(.5))*(vec2(2.0)/viewport.zw)-vec2(1.0);gl_Position=vec4(xy,position.z*2.0-1.0,1.0)/position.w;');
   if(name==='screen-snap'||name==='screen-snap-up')s=s.replace(old,`vec2 screen=${name==='screen-snap'?'roundEven((position.xy-viewport.xy)*256.0)':'floor((position.xy-viewport.xy)*256.0+vec2(.5))'}*(1.0/256.0);vec2 xy=(screen+vec2(.5))/viewport.zw;gl_Position=vec4(xy.x*2.0-1.0,xy.y*2.0-1.0,position.z*2.0-1.0,1.0)/position.w;`);
   if(name==='color-rcp'||name==='clip-color'){assert.ok(s.includes('vColor=diffuse.bgra;'));s=s.replace('vColor=diffuse.bgra;','vColor=floor(diffuse.bgra*255.0+vec4(.5))*(1.0/255.0);');}
  }
  writeFileSync(resolve(dest,file),s);
 }
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,...sources,resolve(dest,'Renderer.cpp'),'-o',resolve(dest,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:dest,TMP:dest,TMPDIR:dest},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(dest,'build.json'),JSON.stringify({diagnosticOnly:true,name,productionRendererChanged:false,sources:Object.fromEntries(files.map(f=>[f,sha(readFileSync(resolve(dest,f)))])),fixtureSources:Object.fromEntries(sources.map(f=>[f,sha(readFileSync(resolve(root,f)))])),wasmSha256:sha(readFileSync(resolve(dest,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(dest,'gpu.mjs'))),nativeSha256:base.nativeSha256,flags},null,2)+'\n');
 console.log('Built original shape candidate '+name);
}
