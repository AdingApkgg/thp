// Independent copies only: test arithmetic hypotheses without changing a release.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/gpu-stage-fog-rounding'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex');
const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','AlphaConversion.hpp','ResampleShader.hpp','Shaders.hpp'];
const flags=JSON.parse(readFileSync(resolve(root,'artifacts/th14/gpu-stage-fog/before/build.json'))).flags;
const variants=['depth-split','term-barrier','range-mul-rsq','vertex-clamp'];
for(const name of variants){
 const destination=resolve(out,name);mkdirSync(destination,{recursive:true});
 for(const file of files){let s=readFileSync(resolve(root,'runtimes/th12/portable/sdl',file),'utf8');
  if(file==='Shaders.hpp'){
   const ratio='(fogParams.y-z)/(fogParams.y-fogParams.x)',split='fogParams.y/(fogParams.y-fogParams.x)-z/(fogParams.y-fogParams.x)';assert(s.includes(ratio));
   s=s.replace(ratio,`(rangeFog?${ratio}:(${split}))`);
   if(name==='term-barrier'){
    s=s.replace('uniform vec3 fogParams;','uniform vec3 fogParams;\nuniform uint roundingFence;');s=s.replace('void main(){','float roundTerm(float v){return uintBitsToFloat(floatBitsToUint(v)^roundingFence);}\nvoid main(){');
    s=s.replace(split,'roundTerm(fogParams.y/(fogParams.y-fogParams.x))-roundTerm(z/(fogParams.y-fogParams.x))');
   }
   if(name==='range-mul-rsq')s=s.replace('length(eye.xyz)','dot(eye.xyz,eye.xyz)*inversesqrt(dot(eye.xyz,eye.xyz))');
   if(name==='vertex-clamp')s=s.replace('transformed?specular.a:fog','transformed?specular.a:clamp(fog,0.0,1.0)');
  }
  writeFileSync(resolve(destination,file),s);
 }
 const fixture='runtimes/th12/th12_web/tests/cpp/th14-gpu-stage-fog-fixture.cpp';
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,fixture,resolve(destination,'Renderer.cpp'),'-o',resolve(destination,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:destination,TMP:destination,TMPDIR:destination},stdio:'inherit',windowsHide:true});
 const sourceHashes=Object.fromEntries(files.map(p=>[p,sha(readFileSync(resolve(destination,p)))]));
 writeFileSync(resolve(destination,'build.json'),JSON.stringify({name,diagnosticOnly:true,completeGame:false,nativeEquivalent:false,sources:sourceHashes,fixtureSha256:sha(readFileSync(resolve(root,fixture))),wasmSha256:sha(readFileSync(resolve(destination,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(destination,'gpu.mjs'))),nativeSha256:sha(readFileSync(resolve(root,'artifacts/th14/gpu-stage-fog/native.json'))),profilesSha256:sha(readFileSync(resolve(root,'artifacts/th14/gpu-stage-fog/profiles.json'))),flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built fog rounding '+name);
}
let html=readFileSync(resolve(root,'tools/th14-gpu-stage-fog.html'),'utf8');
html=html.replace(/<nav>.*?<\/nav>/s,'<nav>'+variants.map(v=>`<a href="/?variant=${v}">${v}</a>`).join(' / ')+'</nav>');
html=html.replaceAll("'before'","'depth-split'").replace("['depth-split','candidate','rsqrt','negative','cpu','rcp-uniform','rcp-barrier']",JSON.stringify(variants));
html=html.replace('differences.length<32','differences.length<native.cases.length');
mkdirSync(out,{recursive:true});writeFileSync(resolve(out,'index.html'),html);
