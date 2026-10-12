import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-world'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';
const build=JSON.parse(readFileSync(resolve(out,'build.json'))),flags=build.flags;
const variants={control:'mix(fogColor.rgb,c.rgb,clamp(vFog,0.0,1.0))',separate:'fogColor.rgb*(1.0-clamp(vFog,0.0,1.0))+c.rgb*clamp(vFog,0.0,1.0)',lerp:'fogColor.rgb+(c.rgb-fogColor.rgb)*clamp(vFog,0.0,1.0)',reverse:'c.rgb+(fogColor.rgb-c.rgb)*(1.0-clamp(vFog,0.0,1.0))'};
const floatMode=process.argv.includes('--float');
if(floatMode){for(const name of Object.keys(variants))delete variants[name];for(const channel of ['r','g','b','a'])variants['float-'+channel]=channel;}
const fogValueMode=process.argv.includes('--fog-value');
if(fogValueMode){for(const name of Object.keys(variants))delete variants[name];variants['float-fog']='clamp(vFog,0.0,1.0)';}
const factorMode=process.argv.includes('--fog-factors');
const factorAnchor='float fog=fogMode==1?exp(-fogParams.z*z):fogMode==2?exp(-pow(fogParams.z*z,2.0)):(fogParams.y-z)/(fogParams.y-fogParams.x);';
if(factorMode){for(const name of Object.keys(variants))delete variants[name];Object.assign(variants,{
 'scaled':'float scale=1.0/(fogParams.y-fogParams.x);float fog=fogMode==1?exp(-fogParams.z*z):fogMode==2?exp(-pow(fogParams.z*z,2.0)):(fogParams.y-z)*scale;',
 'mad':'float scale=1.0/(fogParams.y-fogParams.x);float fog=fogMode==1?exp(-fogParams.z*z):fogMode==2?exp(-pow(fogParams.z*z,2.0)):fogParams.y*scale-z*scale;',
 'squared':'float fog=fogMode==1?exp(-fogParams.z*z):fogMode==2?exp(-fogParams.z*fogParams.z*z*z):(fogParams.y-z)/(fogParams.y-fogParams.x);',
 'exp2':'float fog=fogMode==1?exp2(-fogParams.z*z*1.4426950408889634):fogMode==2?exp2(-pow(fogParams.z*z,2.0)*1.4426950408889634):(fogParams.y-z)/(fogParams.y-fogParams.x);',
 'prepared':'float scale=1.0/(fogParams.y-fogParams.x);float density=fogParams.z*1.4426950408889634;float density2=fogParams.z*fogParams.z*1.4426950408889634;float fog=fogMode==1?exp2(-density*z):fogMode==2?exp2(-density2*z*z):fogParams.y*scale-z*scale;'
});}
for(const [name,expression] of Object.entries(variants)){
 const destination=resolve(out,'variants',name);mkdirSync(destination,{recursive:true});
 for(const file of ['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp']){
  let bytes=readFileSync(resolve(root,'runtimes/th12/portable/sdl',file));if(file==='Shaders.hpp'){
   const source=bytes.toString('utf8'),anchor=floatMode||fogValueMode?'outColor=c;':factorMode?factorAnchor:variants.control;assert.ok(source.includes(anchor));
   const replacement=floatMode||fogValueMode?`highp uint n=floatBitsToUint(${fogValueMode?expression:'c.'+expression});outColor=vec4(float(n&255u),float((n>>8)&255u),float((n>>16)&255u),float((n>>24)&255u))/255.0;`:expression;
   bytes=Buffer.from(source.replace(anchor,replacement));
  }writeFileSync(resolve(destination,file),bytes);
 }
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,'runtimes/th12/th12_web/tests/cpp/th14-gpu-world-fixture.cpp',resolve(destination,'Renderer.cpp'),'-o',resolve(destination,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:destination,TMP:destination,TMPDIR:destination},stdio:'inherit',windowsHide:true});
 const sources=Object.fromEntries(['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'].map(file=>[file,sha(readFileSync(resolve(destination,file)))]));
 writeFileSync(resolve(destination,'build.json'),JSON.stringify({diagnosticOnly:true,name,expression,sources,wasmSha256:sha(readFileSync(resolve(destination,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(destination,'gpu.mjs'))),nativeSha256:build.nativeSha256,flags},null,2)+'\n');console.log('Built diagnostic fog variant '+name);
}
