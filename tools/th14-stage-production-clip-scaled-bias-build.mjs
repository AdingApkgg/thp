// Freeze current production sources and build separate color/UV diagnostics.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/stage-current-production-clip-scaled-bias-oct14'),sdk=resolve(root,'runtimes/th12/tools/emsdk');
const sha=b=>createHash('sha256').update(b).digest('hex');
mkdirSync(out,{recursive:true});
assert(!existsSync(resolve(out,'capture-complete.json')),'Completed capture is immutable');
const original='runtimes/th12/portable/sdl/',files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp'];
const fixturePath='runtimes/th12/th12_web/tests/cpp/th14-stage-gpu-stream-fixture.cpp';
const bindings=Object.fromEntries([...files.map(f=>original+f),fixturePath].map(p=>[p,{bytes:readFileSync(resolve(root,p)).length,sha256:sha(readFileSync(resolve(root,p)))}]));
const snapshot=resolve(out,'source');mkdirSync(snapshot,{recursive:true});
for(const f of files)writeFileSync(resolve(snapshot,f),readFileSync(resolve(root,original+f)));
const baseFixture=readFileSync(resolve(root,fixturePath),'utf8').replace('../../../portable/sdl/Renderer.hpp','Renderer.hpp');
writeFileSync(resolve(snapshot,'fixture.cpp'),baseFixture);
const oldFixturePath='artifacts/th14/stage-gpu-stream-replay/variants/world-uv-production/fixture.cpp';
const oldFixture=readFileSync(resolve(root,oldFixturePath),'utf8'),floatAnchor='EM_JS(int, float_begin_js, (), {';
assert.equal(oldFixture.split(floatAnchor).length,2);const floatFixture=floatAnchor+oldFixture.split(floatAnchor)[1];
const exports=['gpu_allocate','gpu_release','gpu_initialize','gpu_error','gpu_texture','gpu_begin','gpu_render_state','gpu_sampler','gpu_texture_stage','gpu_bind','gpu_fvf','gpu_matrix','gpu_viewport','gpu_clear','gpu_draw','gpu_read','sdl_stats'];
const commonFlags=['-O2','-g0','-std=c++17','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','--use-port=sdl3','--no-entry','-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web','-sALLOW_MEMORY_GROWTH=1','-sMIN_WEBGL_VERSION=2','-sMAX_WEBGL_VERSION=2','-sGL_SUPPORT_AUTOMATIC_ENABLE_EXTENSIONS=0','-sEXPORTED_RUNTIME_METHODS=HEAPU8'];
const builds=[];
for(const name of ['color','uv']){
 const target=resolve(out,name);mkdirSync(target,{recursive:true});
 for(const file of files){let s=readFileSync(resolve(snapshot,file),'utf8');
  if(name==='uv'&&file==='Shaders.hpp'){assert.equal(s.split('outColor=c;').length,2);s=s.replace('outColor=c;','outColor=vec4(vUV,0.0,1.0);');}
  writeFileSync(resolve(target,file),s);
 }
 writeFileSync(resolve(target,'fixture.cpp'),baseFixture+(name==='uv'?'\n'+floatFixture:''));
 const functions=name==='uv'?[...exports,'gpu_float_begin','gpu_float_read']:exports;
 const flags=[...commonFlags,'-sEXPORTED_FUNCTIONS='+functions.map(n=>'_'+n).join(',')];
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,resolve(target,'fixture.cpp'),resolve(target,'Renderer.cpp'),'-o',resolve(target,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:target,TMP:target,TMPDIR:target},stdio:'inherit',windowsHide:true});
 const build={diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,label:'Sourceproduction-clip-scaled-bias-oct14',sourceBindings:bindings,sources:Object.fromEntries([...files,'fixture.cpp'].map(f=>[f,{bytes:readFileSync(resolve(target,f)).length,sha256:sha(readFileSync(resolve(target,f)))}])),wasmSha256:sha(readFileSync(resolve(target,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(target,'gpu.mjs'))),flags,toolSha256:sha(readFileSync(import.meta.filename)),floatFixtureBinding:name==='uv'?{path:oldFixturePath,sha256:sha(Buffer.from(oldFixture))}:null,vertexSourceChanged:false,fragmentUVOverride:name==='uv'};
 writeFileSync(resolve(target,'build.json'),JSON.stringify(build,null,2)+'\n');builds.push({name,buildSha256:sha(readFileSync(resolve(target,'build.json')))});
 console.log('Built current graphics',name,build.wasmSha256);
}
writeFileSync(resolve(out,'sources.json'),JSON.stringify({label:'Sourceproduction-clip-scaled-bias-oct14',sourceBindings:bindings,snapshots:Object.fromEntries([...files,'fixture.cpp'].map(f=>[f,sha(readFileSync(resolve(snapshot,f)))])),builds,toolSha256:sha(readFileSync(import.meta.filename)),scope:'Current production source snapshot after TH14-only CPU sequential clip composition, scaled bias and non-finite numerator fallback. Production Renderer/vertex shader copied byte-for-byte; old candidate hashes are not inherited. Color module is unchanged; UV module replaces fragment color output only and adds isolated float target readback.'},null,2)+'\n');


