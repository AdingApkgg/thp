import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-world-profiles'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const python=process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';
const base=JSON.parse(readFileSync(resolve(root,'artifacts/th14/gpu-world/build.json'))),flags=base.flags.map(f=>f.replace('_gpu_world_case','_gpu_world_profile_case'));
const flat=process.argv.includes('--flat-fog');
const fixture=flat?'runtimes/th12/th12_web/tests/cpp/th14-gpu-world-flat-fixture.cpp':'runtimes/th12/th12_web/tests/cpp/th14-gpu-world-profiles-fixture.cpp';
const reciprocal=process.argv.includes('--reciprocal');
const correctBlend=process.argv.includes('--correct-blend');
const fogBlend=process.argv.includes('--fog-blend')||correctBlend;
const floatEuler=process.argv.includes('--float-euler');
const floatColors=process.argv.includes('--float-colors');
const fogColor=process.argv.includes('--fog-color')||floatColors||correctBlend;
const cpu=process.argv.includes('--cpu-fog'),floatFog=process.argv.includes('--float-fog')||flat||floatEuler,eulerUniform=process.argv.includes('--euler-uniform')||fogColor,euler=process.argv.includes('--euler-base')||eulerUniform||reciprocal||floatEuler;
for(const name of correctBlend?['correct-lerp','correct-reverse','correct-separate']:floatColors?['float-color-r','float-color-g','float-color-b','float-color-a']:fogColor?['euler-color']:floatEuler?['float-euler-base','float-euler-uniform']:fogBlend?['euler-lerp','euler-reverse','euler-separate']:reciprocal?['euler-reciprocal','reciprocal-uniform']:euler?[eulerUniform?'euler-uniform':'euler-base']:floatFog?[flat?'float-flat':'float-fog']:cpu?['cpu-scale','cpu-exp','cpu-both']:['control','squared']){
 const destination=resolve(out,name);mkdirSync(destination,{recursive:true});
 for(const file of ['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp']){
  let bytes=readFileSync(resolve(root,'runtimes/th12/portable/sdl',file));if(name==='squared'&&file==='Shaders.hpp'){
   const source=bytes.toString('utf8'),anchor='exp(-pow(fogParams.z*z,2.0))';assert.ok(source.includes(anchor));bytes=Buffer.from(source.replace(anchor,'exp(-fogParams.z*fogParams.z*z*z)'));
  }
  const scale=name==='cpu-scale'||name==='cpu-both',exponent=name==='cpu-exp'||name==='cpu-both';
  if((scale||exponent)&&file==='Renderer.cpp'){
   let source=bytes.toString('utf8');const anchor='float fog[]{p.fogNear,p.fogFar,p.fogDensity};';assert.ok(source.includes(anchor));
   const density=exponent?'p.fogMode==FogMode::Exponential?p.fogDensity*1.4426950408889634f:p.fogMode==FogMode::ExponentialSquared?p.fogDensity*p.fogDensity*1.4426950408889634f:p.fogDensity':'p.fogDensity';
   source=source.replace(anchor,`float fog[]{${scale?'1.0f/(p.fogFar-p.fogNear)':'p.fogNear'},p.fogFar,${density}};`);bytes=Buffer.from(source);
  }
  if((scale||exponent)&&file==='Shaders.hpp'){
   let source=bytes.toString('utf8');
   if(scale){const anchor='(fogParams.y-z)/(fogParams.y-fogParams.x)';assert.ok(source.includes(anchor));source=source.replace(anchor,'(fogParams.y-z)*fogParams.x');}
   if(exponent){const anchor='exp(-fogParams.z*z):fogMode==2?exp(-pow(fogParams.z*z,2.0))';assert.ok(source.includes(anchor));source=source.replace(anchor,'exp2(-fogParams.z*z):fogMode==2?exp2(-fogParams.z*z*z)');}
   bytes=Buffer.from(source);
  }
  if((euler||fogBlend)&&file==='Shaders.hpp'){
   const source=bytes.toString('utf8'),anchor='exp(-fogParams.z*z):fogMode==2?exp(-pow(fogParams.z*z,2.0))';assert.ok(source.includes(anchor));
   const base=(eulerUniform||name.endsWith('uniform'))?'fogParams.x':'2.71828';
   bytes=Buffer.from(source.replace(anchor,reciprocal?`1.0/pow(${base},fogParams.z*z):fogMode==2?1.0/pow(${base},pow(fogParams.z*z,2.0))`:`pow(${base},-fogParams.z*z):fogMode==2?pow(${base},-pow(fogParams.z*z,2.0))`));
  }
  if(fogBlend&&file==='Shaders.hpp'){
   const source=bytes.toString('utf8'),anchor='mix(fogColor.rgb,c.rgb,clamp(vFog,0.0,1.0))';assert.ok(source.includes(anchor));
   const expression=name.endsWith('lerp')?'fogColor.rgb+(c.rgb-fogColor.rgb)*clamp(vFog,0.0,1.0)':name.endsWith('reverse')?'c.rgb+(fogColor.rgb-c.rgb)*(1.0-clamp(vFog,0.0,1.0))':'c.rgb*clamp(vFog,0.0,1.0)+fogColor.rgb*(1.0-clamp(vFog,0.0,1.0))';
   bytes=Buffer.from(source.replace(anchor,expression));
  }
  if((eulerUniform||name.endsWith('uniform'))&&file==='Renderer.cpp'){
   const source=bytes.toString('utf8'),anchor='float fog[]{p.fogNear,p.fogFar,p.fogDensity};';assert.ok(source.includes(anchor));
   bytes=Buffer.from(source.replace(anchor,'float fog[]{p.fogMode==FogMode::Exponential||p.fogMode==FogMode::ExponentialSquared?2.71828f:p.fogNear,p.fogFar,p.fogDensity};'));
  }
  if(fogColor&&file==='Renderer.cpp'){
   const source=bytes.toString('utf8'),anchor=source.match(/^std::array<float,4> color.*$/m)?.[0];assert.ok(anchor);assert.ok(source.includes('color(p.fogColor).data()'));
   bytes=Buffer.from(source.replace(anchor,anchor+'\n'+anchor.replace(' color',' fog_color').replaceAll('/255','*(1.f/255.f)')).replace('color(p.fogColor).data()','fog_color(p.fogColor).data()'));
  }
  if((floatFog||floatColors)&&file==='Shaders.hpp'){
   const source=bytes.toString('utf8'),anchor='outColor=c;';assert.ok(source.includes(anchor));
   const value=floatColors?'c.'+name.at(-1):'clamp(vFog,0.0,1.0)';bytes=Buffer.from(source.replace(anchor,`highp uint raw=floatBitsToUint(${value});outColor=vec4(float(raw&255u),float((raw>>8u)&255u),float((raw>>16u)&255u),float((raw>>24u)&255u))/255.0;`));
  }writeFileSync(resolve(destination,file),bytes);
 }
 execFileSync(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,fixture,resolve(destination,'Renderer.cpp'),'-o',resolve(destination,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:destination,TMP:destination,TMPDIR:destination},stdio:'inherit',windowsHide:true});
 const sources=Object.fromEntries(['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'].map(file=>[file,sha(readFileSync(resolve(destination,file)))]));
 writeFileSync(resolve(destination,'build.json'),JSON.stringify({diagnosticOnly:true,name,sources,fixtureSha256:sha(readFileSync(resolve(root,fixture))),wasmSha256:sha(readFileSync(resolve(destination,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(destination,'gpu.mjs'))),nativeSha256:sha(readFileSync(resolve(out,'native.json'))),flags},null,2)+'\n');console.log('Built fog profiles '+name);
}
