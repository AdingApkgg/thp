import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-screen-grid'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',base=JSON.parse(readFileSync(resolve(root,'artifacts/th14/gpu-original-shapes/build.json')));
const flags=base.flags.map(f=>f.replace('_gpu_original_shape_case','_gpu_screen_grid_case'));
const sources=Object.keys(base.sources).filter(p=>p.endsWith('.cpp')&&!p.endsWith('th14-render-fixture.cpp')&&!p.endsWith('portable/sdl/Renderer.cpp')).map(p=>p.replace('th14-gpu-original-shapes-fixture.cpp','th14-gpu-screen-grid-fixture.cpp'));
for(const name of ['before','screen-snap']){
 const dest=resolve(out,name);mkdirSync(dest,{recursive:true});
 const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'];
 const from=resolve(root,name==='before'?'runtimes/th12/portable/sdl':'artifacts/th14/gpu-original-shapes/screen-snap');for(const f of files)writeFileSync(resolve(dest,f),readFileSync(resolve(from,f)));
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,...sources,resolve(dest,'Renderer.cpp'),'-o',resolve(dest,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:dest,TMP:dest,TMPDIR:dest},stdio:'inherit',windowsHide:true});
 const fixtureFiles=[...sources,'runtimes/th12/th12_web/tests/cpp/th14-gpu-screen-grid-data.hpp','runtimes/th12/th12_web/tests/cpp/th14-gpu-original-shapes-fixture.cpp','runtimes/th12/th12_web/tests/cpp/th14-gpu-original-shapes-data.hpp','runtimes/th12/th12_web/tests/cpp/th14-render-fixture.cpp','runtimes/th12/th12_web/tests/cpp/render-fixture.hpp'];
 writeFileSync(resolve(dest,'build.json'),JSON.stringify({diagnosticOnly:true,name,sources:Object.fromEntries(files.map(f=>[f,sha(readFileSync(resolve(dest,f)))])),fixtureSources:Object.fromEntries(fixtureFiles.map(f=>[f,sha(readFileSync(resolve(root,f)))])),wasmSha256:sha(readFileSync(resolve(dest,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(dest,'gpu.mjs'))),nativeSha256:sha(readFileSync(resolve(out,'native.json'))),flags},null,2)+'\n');console.log('Built subpixel grid '+name);
}
