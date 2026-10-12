// Isolated clip-matrix hypotheses; the production renderer stays untouched.
import assert from 'node:assert/strict';import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';import {resolve} from 'node:path';import {createHash} from 'node:crypto';import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-gpu-stream-replay'),sdk=resolve(root,'runtimes/th12/tools/emsdk'),sha=b=>createHash('sha256').update(b).digest('hex'),before=JSON.parse(readFileSync(resolve(base,'build.json')));
for(const name of ['unbatched-control','cpu-float-clip','cpu-pair-clip']){
 const out=resolve(base,'variants',name);mkdirSync(out,{recursive:true});const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp'];
 for(const file of files){let s=readFileSync(resolve(root,'runtimes/th12/portable/sdl',file),'utf8');
  if(name!=='unbatched-control'&&file==='Shaders.hpp'){assert(s.includes('gl_Position=projection*eye;'));s=s.replace('uniform mat4 world,view,projection,textureMatrix;','uniform mat4 world,view,projection,textureMatrix,clipMatrix;').replace('gl_Position=projection*eye;','gl_Position=clipMatrix*vec4(position.xyz,1.0);');}
  if(name!=='unbatched-control'&&file==='Renderer.cpp'){
   const names='"depth16","tex"';assert(s.includes(names));s=s.replace(names,names+',"clipMatrix"');
   assert(s.includes('i<26;i++'));s=s.replace('i<26;i++','i<27;i++');
   const anchor='integer(1,transformed);';assert(s.includes(anchor));
   const sum=name==='cpu-pair-clip'?'float a=A[row]*B[col*4]+A[4+row]*B[col*4+1];float b=A[8+row]*B[col*4+2]+A[12+row]*B[col*4+3];C[col*4+row]=a+b;':'float sum=A[row]*B[col*4];for(int k=1;k<4;k++)sum+=A[k*4+row]*B[col*4+k];C[col*4+row]=sum;';
   const combine='auto multiply=[](const std::array<float,16>& A,const std::array<float,16>& B){std::array<float,16>C{};for(int col=0;col<4;col++)for(int row=0;row<4;row++){'+sum+'}return C;};auto combined=multiply(d.matrix[2],multiply(d.matrix[1],d.matrix[0]));uniform(26,16,combined.data());\n ';
   s=s.replace(anchor,combine+anchor);
  }writeFileSync(resolve(out,file),s);
 }
 let fixture=readFileSync(resolve(root,'runtimes/th12/th12_web/tests/cpp/th14-stage-gpu-stream-fixture.cpp'),'utf8').replace('../../../portable/sdl/Renderer.hpp','Renderer.hpp');
 const draw='renderer->draw(Topology::Strip,count,words,stride);return 1;';assert(fixture.includes(draw));fixture=fixture.replace(draw,'renderer->draw(Topology::Strip,count,words,stride);renderer->flush();return 1;');writeFileSync(resolve(out,'fixture.cpp'),fixture);
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(out,'fixture.cpp'),resolve(out,'Renderer.cpp'),'-o',resolve(out,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:out,TMP:out,TMPDIR:out},stdio:'inherit',windowsHide:true});
 writeFileSync(resolve(out,'build.json'),JSON.stringify({diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,baseBuildSha256:sha(readFileSync(resolve(base,'build.json'))),sources:Object.fromEntries([...files,'fixture.cpp'].map(p=>[p,sha(readFileSync(resolve(out,p)))])),wasmSha256:sha(readFileSync(resolve(out,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(out,'gpu.mjs'))),flags:before.flags,toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');console.log('Built isolated clip transform',name);
}
