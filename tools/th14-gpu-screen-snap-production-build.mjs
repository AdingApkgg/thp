import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-screen-snap-production'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',rt='runtimes/th12/th12_web/';
const specs={shapes:['gpu-original-shapes','th14-gpu-original-shapes-fixture.cpp'],quads:['gpu-original-quads','th14-gpu-original-quads-fixture.cpp'],grid:['gpu-screen-grid','th14-gpu-screen-grid-fixture.cpp'],raster:['gpu-raster','th14-gpu-raster-fixture.cpp'],alpha:['gpu-alpha','th14-gpu-alpha-fixture.cpp'],'alpha-blend':['gpu-alpha-blend','th14-gpu-alpha-blend-fixture.cpp'],'alpha-depth':['gpu-alpha-depth','th14-gpu-alpha-depth-fixture.cpp']};
for(const suite of process.argv.slice(2).length?process.argv.slice(2):Object.keys(specs)){
 const [ref,fixtureName]=specs[suite],reference=resolve(root,'artifacts/th14',ref),base=JSON.parse(readFileSync(resolve(reference,suite==='grid'?'before/build.json':'build.json'))),dest=resolve(out,suite);mkdirSync(dest,{recursive:true});
 const flags=base.flags.filter(f=>!f.startsWith('-DPORT_TITLE=')).concat('-DPORT_TITLE=14');
 const gameSources=['AnmVm','AnmResource','AnmInterpreter','AnmGeometry','AnmProjection','AnmRenderer','GraphicsMath','Interpolation','SceneCamera'].map(n=>rt+`cpp/game/${n}.cpp`);
 const sources=[...(['shapes','quads','grid'].includes(suite)?gameSources:[]),rt+'tests/cpp/'+fixtureName,'runtimes/th12/portable/sdl/Renderer.cpp'];
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,...sources,'-o',resolve(dest,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:dest,TMP:dest,TMPDIR:dest},stdio:'inherit',windowsHide:true});
 const deps=Object.keys(base.sources).filter(p=>p.includes('/')&&!p.startsWith('tools/')).concat(Object.keys(base.fixtureSources||{}));
 if(suite==='grid')deps.push(rt+'tests/cpp/th14-gpu-screen-grid-data.hpp',rt+'tests/cpp/th14-gpu-original-shapes-fixture.cpp',rt+'tests/cpp/th14-gpu-original-shapes-data.hpp',rt+'tests/cpp/th14-render-fixture.cpp',rt+'tests/cpp/render-fixture.hpp');
 const rendererFiles=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'].map(n=>'runtimes/th12/portable/sdl/'+n);
 const files=[...new Set([...sources,...deps,...rendererFiles])];
 const native=JSON.parse(readFileSync(resolve(reference,'native.json')));assert.equal(native.generated,true);
 writeFileSync(resolve(dest,'build.json'),JSON.stringify({built:true,title:14,usesCurrentProductionRenderer:true,suite,completeGame:false,nativeEquivalent:false,sources:Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(root,p)))])),wasmSha256:sha(readFileSync(resolve(dest,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(dest,'gpu.mjs'))),nativeSha256:sha(readFileSync(resolve(reference,'native.json'))),nativeLowSha256:suite==='alpha'?sha(readFileSync(resolve(root,'artifacts/th14/gpu-alpha-low/native.json'))):undefined,flags},null,2)+'\n');console.log('Built current production TH14 GPU '+suite);
}
