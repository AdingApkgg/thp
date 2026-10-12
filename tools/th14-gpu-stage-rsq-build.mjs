import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-stage-fog'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';
const fixture='runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-flat-float-fixture.cpp',flags=JSON.parse(readFileSync(resolve(root,'artifacts/th14/gpu-world/build.json'))).flags.map(f=>f.replace('_gpu_world_case','_gpu_stage_direct_float_case'));
for(const base of ['candidate']){
 const name='flat-probe-rsq',destination=resolve(out,name);mkdirSync(destination,{recursive:true});
 for(const file of ['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp']){
  let source=readFileSync(resolve(out,base,file),'utf8');
  if(file==='Shaders.hpp'){const expression='vFog=fogEnabled?(transformed?specular.a:fog):1.0;';assert.ok(source.includes(expression));source=source.replace(expression,'vFog=fogEnabled?inversesqrt(dot(eye.xyz,eye.xyz)):1.0;');
   const anchor='outColor=c;';assert.equal(source.split(anchor).length,2);source=source.replace(anchor,'outColor=vec4(vec3(fogEnabled?clamp(vFog,0.0,1.0):1.0),c.a);');
  }
  if(file==='Renderer.hpp'){const anchor='const float* alpha_boundaries()const{return alphaBoundaries.data();}';assert.ok(source.includes(anchor));source=source.replace(anchor,anchor+'\n    const float* diagnostic_float_pixels()const{return reinterpret_cast<const float*>(pixels.data());}');}
  if(file==='Renderer.cpp'){
   const init='if(version==10&&!measure_alpha_boundaries(alphaBoundaries))';assert.ok(source.includes(init));
   source=source.replace(init,'if(!touhou_float_target()){failure="EXT_color_buffer_float unavailable";return false;}\n '+init);
   source=source.replace('EM_JS(int, touhou_clip_control, (), {','EM_JS(int,touhou_float_target,(),{return !!GL.currentContext.GLctx.getExtension("EXT_color_buffer_float");});\nEM_JS(int, touhou_clip_control, (), {');
   const image='if(g.version==~0u)glTexImage2D(';assert.ok(source.includes(image));source=source.replace(image,'if(h==1)glTexImage2D(GL_TEXTURE_2D,0,GL_RGBA32F,s.width,s.height,0,GL_RGBA,GL_FLOAT,nullptr);else '+image);
   const start=source.indexOf('void Renderer::read(u32 id)'),end=source.indexOf('void Renderer::release(u32 id)');assert.ok(start>=0&&end>start);
   source=source.slice(0,start)+'void Renderer::read(u32 id){flush();auto it=surfaces.find(id);if(it==surfaces.end()||!it->second.rendered)return;auto s=resolve(owner,id);pixels.resize(s.width*s.height*16);bind_framebuffer(GL_FRAMEBUFFER,it->second.framebuffer);glPixelStorei(GL_PACK_ALIGNMENT,1);glReadPixels(0,0,s.width,s.height,GL_RGBA,GL_FLOAT,pixels.data());it->second.rendered=false;}\n'+source.slice(end);
   source+='\nextern "C" const float* gpu_diagnostic_float_pixels(){return touhou::sdl::current()->diagnostic_float_pixels();}\n';
  }
  writeFileSync(resolve(destination,file),source);
 }
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,fixture,resolve(destination,'Renderer.cpp'),'-o',resolve(destination,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:destination,TMP:destination,TMPDIR:destination},stdio:'inherit',windowsHide:true});
 const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'];
 writeFileSync(resolve(destination,'build.json'),JSON.stringify({diagnosticOnly:true,name,base,outputFormat:'RGBA32F',shaderUnmodifiedFromBase:false,shaderSha256:sha(readFileSync(resolve(destination,'Shaders.hpp'))),sources:Object.fromEntries(files.map(f=>[f,sha(readFileSync(resolve(destination,f)))])),fixtureSha256:sha(readFileSync(resolve(root,fixture))),profileFixtureSha256:sha(readFileSync(resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-flat-probe-fixture.cpp'))),wasmSha256:sha(readFileSync(resolve(destination,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(destination,'gpu.mjs'))),nativeSha256:sha(readFileSync(resolve(root,'artifacts/th14/gpu-native-shader-probe/rsq-output/native.json'))),flags},null,2)+'\n');console.log('Built '+name);
}
