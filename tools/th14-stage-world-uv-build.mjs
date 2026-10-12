import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
for(const name of ['world-uv-production','world-uv-cpu-clip']){
 const out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const original=name==='world-uv-production',source=original?resolve(root,'runtimes/th12/portable/sdl'):resolve(base,'variants/cpu-clip-depth-fixed20'),before=JSON.parse(readFileSync(resolve(base,original?'build.json':'variants/cpu-clip-depth-fixed20/build.json'))),files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp'];
 for(const file of files){let s=readFileSync(resolve(source,file),'utf8');if(file==='Shaders.hpp'){assert(s.includes('outColor=c;'));s=s.replace('outColor=c;','outColor=vec4(vUV,0.0,1.0);');}writeFileSync(resolve(out,file),s);}
 let fixture=original?readFileSync(resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-stage-gpu-stream-fixture.cpp'),'utf8').replace('../../../portable/sdl/Renderer.hpp','Renderer.hpp'):readFileSync(resolve(source,'fixture.cpp'),'utf8');
 fixture+=`
EM_JS(int, float_begin_js, (), {
 const gl=GL.currentContext.GLctx;if(!gl.getExtension('EXT_color_buffer_float'))throw Error('EXT_color_buffer_float unavailable');
 const saved=gl.getParameter(gl.TEXTURE_BINDING_2D);let tex=Module.floatProbeTexture;
 if(!tex){tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA32F,640,480,0,gl.RGBA,gl.FLOAT,null);Module.floatProbeTexture=tex;}
 gl.framebufferTexture2D(gl.FRAMEBUFFER,gl.COLOR_ATTACHMENT0,gl.TEXTURE_2D,tex,0);gl.bindTexture(gl.TEXTURE_2D,saved);if(gl.checkFramebufferStatus(gl.FRAMEBUFFER)!==gl.FRAMEBUFFER_COMPLETE)throw Error('Float UV framebuffer');return 1;
});
EM_JS(int, float_read_js, (void* output), {const gl=GL.currentContext.GLctx;gl.readPixels(0,0,640,480,gl.RGBA,gl.FLOAT,HEAPF32.subarray(output>>2,(output>>2)+640*480*4));const e=gl.getError();if(e)throw Error('Float UV read error '+e);return 1;});
extern "C" EMSCRIPTEN_KEEPALIVE int gpu_float_begin(){if(!renderer)return 0;renderer->flush();int r=float_begin_js();renderer->clear(3,0,1,0);return r;}
extern "C" EMSCRIPTEN_KEEPALIVE int gpu_float_read(void* output){if(!renderer)return 0;renderer->flush();return float_read_js(output);}
`;
 writeFileSync(resolve(out,'fixture.cpp'),fixture);const flags=before.flags.map(f=>f.startsWith('-sEXPORTED_FUNCTIONS=')?f+',_gpu_float_begin,_gpu_float_read':f);
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(base,original?'build.json':'variants/cpu-clip-depth-fixed20/build.json'))),sources:Object.fromEntries([...files,'fixture.cpp'].map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built independent FFP varying probe',name);
}
