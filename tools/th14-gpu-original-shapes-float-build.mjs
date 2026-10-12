import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),reference=resolve(root,'artifacts/th14/gpu-original-shapes/float'),snapped=process.argv.includes('--screen-snap'),out=snapped?resolve(reference,'screen-snap'):reference,sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');mkdirSync(out,{recursive:true});
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',base=JSON.parse(readFileSync(resolve(root,'artifacts/th14/gpu-original-shapes/build.json')));
const flags=base.flags,sources=Object.keys(base.sources).filter(p=>p.endsWith('.cpp')&&!p.endsWith('th14-render-fixture.cpp')&&!p.endsWith('portable/sdl/Renderer.cpp')).map(p=>p.replace('th14-gpu-original-shapes-fixture.cpp','th14-gpu-original-shapes-float-fixture.cpp'));
const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'];
for(const file of files){
 let s=readFileSync(resolve(root,snapped?'artifacts/th14/gpu-original-shapes/screen-snap':'runtimes/th12/portable/sdl',file),'utf8');
 if(file==='Renderer.cpp'){
  const init='if(version==10&&!measure_alpha_boundaries(alphaBoundaries))';assert.ok(s.includes(init));
  s=s.replace(init,'if(!touhou_shape_float_target()){failure="EXT_color_buffer_float unavailable";return false;}\n '+init);
  s=s.replace('EM_JS(int, touhou_clip_control, (), {','EM_JS(int,touhou_shape_float_target,(),{return !!GL.currentContext.GLctx.getExtension("EXT_color_buffer_float");});\nEM_JS(int, touhou_clip_control, (), {');
  const target='if(g.version==~0u)glTexImage2D(';assert.ok(s.includes(target));
  s=s.replace(target,'if(h==1)glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA32F,s.width,s.height,0,GL_RGBA,GL_FLOAT,nullptr);else '+target);
  const start=s.indexOf('void Renderer::read(u32 id){'),end=s.indexOf('void Renderer::release(',start);assert.ok(start>=0&&end>start);
  s=s.slice(0,start)+'void Renderer::read(u32 id){flush();auto it=surfaces.find(id);if(it==surfaces.end()||!it->second.rendered)return;auto s=resolve(owner,id);bind_framebuffer(GL_FRAMEBUFFER,it->second.framebuffer);glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,s.width,s.height,GL_RGBA,GL_FLOAT,s.data);it->second.rendered=false;}\n'+s.slice(end);
  s='#include <emscripten/html5.h>\n'+s;
 }
 writeFileSync(resolve(out,file),s);
}
execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,...sources,resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,shaderUnmodified:!snapped,shaderUnmodifiedFromCandidate:snapped,blendingEnabled:false,sources:Object.fromEntries(files.map(f=>[f,sha(readFileSync(resolve(out,f)))])),fixtureSources:Object.fromEntries(sources.map(f=>[f,sha(readFileSync(resolve(root,f)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),nativeSha256:sha(readFileSync(resolve(reference,'native.json'))),flags},null,2)+'\n');
console.log('Built production shape geometry with unchanged shaders into diagnostic RGBA32F target');
