import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-screen-snap-regression'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';
const rendererFiles=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'];
const shared=resolve(out,'renderer');mkdirSync(shared,{recursive:true});for(const f of rendererFiles)writeFileSync(resolve(shared,f),readFileSync(resolve(root,'artifacts/th14/gpu-original-shapes/screen-snap',f)));
for(const suite of process.argv.slice(2).length?process.argv.slice(2):['raster','alpha','alpha-blend','alpha-depth']){
 const baseline='artifacts/th14/gpu-'+suite,base=JSON.parse(readFileSync(resolve(root,baseline,'build.json'))),dest=resolve(out,suite);mkdirSync(dest,{recursive:true});
 const fixture='runtimes/th12/th12_web/tests/cpp/th14-gpu-'+suite+'-fixture.cpp',sources=[fixture,resolve(shared,'Renderer.cpp')];
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...base.flags,...sources,'-o',resolve(dest,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:dest,TMP:dest,TMPDIR:dest},stdio:'inherit',windowsHide:true});
 const fixtureFiles=[fixture,'runtimes/th12/th12_web/tests/cpp/th14-gpu-raster-fixture.cpp'];
 writeFileSync(resolve(dest,'build.json'),JSON.stringify({diagnosticOnly:true,suite,productionChanged:false,sources:Object.fromEntries(rendererFiles.map(f=>[f,sha(readFileSync(resolve(shared,f)))])),fixtureSources:Object.fromEntries(fixtureFiles.map(f=>[f,sha(readFileSync(resolve(root,f)))])),wasmSha256:sha(readFileSync(resolve(dest,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(dest,'gpu.mjs'))),nativeSha256:sha(readFileSync(resolve(root,baseline,'native.json'))),nativeLowSha256:suite==='alpha'?sha(readFileSync(resolve(root,'artifacts/th14/gpu-alpha-low/native.json'))):undefined,flags:base.flags},null,2)+'\n');
 console.log('Built screen-coordinate candidate regression '+suite);
}
