// Independent float32 composition candidate; production sources remain untouched.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),before=resolve(root,'artifacts/th14/stage-current-graphics-fe406-oct14');
const out=resolve(root,'artifacts/th14/stage-current-sequential-clip-homogeneous-fe406-oct14'),sdk=resolve(root,'runtimes/th12/tools/emsdk');
const sha=b=>createHash('sha256').update(b).digest('hex'),label='Sourcefe406-sequential-clip-homogeneous-diagnostic-oct14';
mkdirSync(out,{recursive:true});assert(!existsSync(resolve(out,'capture-complete.json')),'Completed candidate is immutable');
const baseSources=JSON.parse(readFileSync(resolve(before,'sources.json'))),snapshot=resolve(out,'source');mkdirSync(snapshot,{recursive:true});
const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp'];
for(const file of [...files,'fixture.cpp']){
 const b=readFileSync(resolve(before,'source',file));assert.equal(sha(b),baseSources.snapshots[file]);writeFileSync(resolve(snapshot,file),b);
}
const helper=`// Each product and partial sum is a separate binary32 store.
// No captured Native values or host clock inputs occur in this helper.
using DiagnosticMatrix=std::array<float,16>;
static uint32_t diagnosticRegularCompositions=0,diagnosticInstanceBatches=0,diagnosticInstanceCompositions=0;
static DiagnosticMatrix diagnostic_multiply(const DiagnosticMatrix& a,const DiagnosticMatrix& b){
 DiagnosticMatrix result{};
 for(int col=0;col<4;++col)for(int row=0;row<4;++row){
  volatile float product=a[row]*b[col*4];volatile float sum=product;
  for(int k=1;k<4;++k){product=a[k*4+row]*b[col*4+k];sum=sum+product;}
  result[col*4+row]=sum;
 }
 return result;
}
static DiagnosticMatrix diagnostic_clip(const DiagnosticMatrix& world,const DiagnosticMatrix& view,const DiagnosticMatrix& projection){
 return diagnostic_multiply(projection,diagnostic_multiply(view,world));
}
`;
const exports=['gpu_allocate','gpu_release','gpu_initialize','gpu_error','gpu_texture','gpu_begin','gpu_render_state','gpu_sampler','gpu_texture_stage','gpu_bind','gpu_fvf','gpu_matrix','gpu_viewport','gpu_clear','gpu_draw','gpu_read','gpu_clip_regular_count','gpu_clip_instance_batches','gpu_clip_instance_count'];
const builds=[];
for(const name of ['color','uv']){
 const target=resolve(out,name);mkdirSync(target,{recursive:true});
 for(const file of files){let source=readFileSync(resolve(snapshot,file),'utf8');
  if(file==='Shaders.hpp'){
   const anchors=[['layout(location=8) in vec4 instanceFactor;','layout(location=8) in vec4 instanceFactor;\nlayout(location=9) in vec4 instanceClip0;\nlayout(location=10) in vec4 instanceClip1;\nlayout(location=11) in vec4 instanceClip2;\nlayout(location=12) in vec4 instanceClip3;'],
    ['uniform mat4 world,view,projection,textureMatrix;','uniform mat4 world,view,projection,textureMatrix,clipMatrix;'],
    ['gl_Position=projection*eye;','mat4 composed=instanced?mat4(instanceClip0,instanceClip1,instanceClip2,instanceClip3):clipMatrix;gl_Position=composed*vec4(position.xyz,1.0);']];
   for(const [old,value] of anchors){assert.equal(source.split(old).length,2);source=source.replace(old,value);}
   if(name==='uv'){assert.equal(source.split('outColor=c;').length,2);source=source.replace('outColor=c;','outColor=vec4(vUV,0.0,1.0);');}
   const viewportAnchor='gl_Position.xy+=gl_Position.w/viewport.zw;';
   const viewportStep='vec2 worldScale=(viewport.zw*0.5)/gl_Position.w;vec2 worldScreen=(gl_Position.xy+vec2(gl_Position.w))*worldScale;gl_Position.xy=((worldScreen+vec2(0.5))/viewport.zw*2.0-vec2(1.0))*gl_Position.w;';
   assert.equal(source.split(viewportAnchor).length,2);source=source.replace(viewportAnchor,viewportStep);
   assert(source.includes('vec4 eye=view*model*vec4(position.xyz,1.0);'),'Fog eye path unchanged');
  }
  if(file==='Renderer.cpp'){
   const include='#include "Renderer.hpp"';assert.equal(source.split(include).length,2);source=source.replace(include,include+'\n#include "ClipComposition.hpp"');
   assert.equal(source.split('"depth16","tex"').length,2);source=source.replace('"depth16","tex"','"depth16","tex","clipMatrix"');
   assert.equal(source.split('i<26;i++').length,2);source=source.replace('i<26;i++','i<27;i++');
   const uniforms='integer(1,transformed);';assert.equal(source.split(uniforms).length,2);
   source=source.replace(uniforms,'if(!transformed&&!instance){auto clip=diagnostic_clip(d.matrix[0],d.matrix[1],d.matrix[2]);uniform(26,16,clip.data());++diagnosticRegularCompositions;}\n '+uniforms);
   const instance='if(instance){u32 b=upload(instances,GL_ARRAY_BUFFER,instance,instanceSize,65536);';assert.equal(source.split(instance).length,2);
   const expanded=`if(instance){
 // Preserve the original world/factor record for fog and color; append the
 // composed matrix for EACH instance, retaining all batching/strip semantics.
 const u32 records=instanceSize/68;std::vector<u8> expanded(records*132);
 const auto* input=static_cast<const u8*>(instance);
 for(u32 record=0;record<records;++record){
  DiagnosticMatrix model{};std::memcpy(model.data(),input+record*68,64);
  auto clip=diagnostic_clip(model,d.matrix[1],d.matrix[2]);
  std::memcpy(expanded.data()+record*132,input+record*68,68);
  std::memcpy(expanded.data()+record*132+68,clip.data(),64);
 }
 ++diagnosticInstanceBatches;diagnosticInstanceCompositions+=records;
 u32 b=upload(instances,GL_ARRAY_BUFFER,expanded.data(),u32(expanded.size()),65536);`;
   source=source.replace(instance,expanded);
   const attrib='for(int i=0;i<4;i++){glEnableVertexAttribArray(4+i);glVertexAttribPointer(4+i,4,GL_FLOAT,false,68,reinterpret_cast<void*>(b+i*16));glVertexAttribDivisor(4+i,1);}glEnableVertexAttribArray(8);glVertexAttribPointer(8,4,GL_UNSIGNED_BYTE,true,68,reinterpret_cast<void*>(b+64));glVertexAttribDivisor(8,1);}';
   assert.equal(source.split(attrib).length,2);
   source=source.replace(attrib,'for(int i=0;i<4;i++){glEnableVertexAttribArray(4+i);glVertexAttribPointer(4+i,4,GL_FLOAT,false,132,reinterpret_cast<void*>(b+i*16));glVertexAttribDivisor(4+i,1);glEnableVertexAttribArray(9+i);glVertexAttribPointer(9+i,4,GL_FLOAT,false,132,reinterpret_cast<void*>(b+68+i*16));glVertexAttribDivisor(9+i,1);}glEnableVertexAttribArray(8);glVertexAttribPointer(8,4,GL_UNSIGNED_BYTE,true,132,reinterpret_cast<void*>(b+64));glVertexAttribDivisor(8,1);}');
   assert(source.includes('glDrawArraysInstanced(mode,0,n,instanceSize/68);'),'Original instance count retained');
   source+='\nextern "C" {\nuint32_t gpu_clip_regular_count(){return diagnosticRegularCompositions;}\nuint32_t gpu_clip_instance_batches(){return diagnosticInstanceBatches;}\nuint32_t gpu_clip_instance_count(){return diagnosticInstanceCompositions;}\n}\n';
  }
  writeFileSync(resolve(target,file),source);
 }
 writeFileSync(resolve(target,'ClipComposition.hpp'),helper);
 writeFileSync(resolve(target,'fixture.cpp'),readFileSync(resolve(before,name,'fixture.cpp')));
 const prior=JSON.parse(readFileSync(resolve(before,name,'build.json')));
 const functions=name==='uv'?[...exports,'gpu_float_begin','gpu_float_read']:exports;
 const flags=prior.flags.filter(f=>!f.startsWith('-sEXPORTED_FUNCTIONS='));flags.push('-fno-fast-math','-ffp-contract=off','-sEXPORTED_FUNCTIONS='+functions.map(n=>'_'+n).join(','));
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,resolve(target,'fixture.cpp'),resolve(target,'Renderer.cpp'),'-o',resolve(target,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:target,TMP:target,TMPDIR:target},stdio:'inherit',windowsHide:true});
 const build={diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name,label,sourceBindings:baseSources.sourceBindings,
  sources:Object.fromEntries([...files,'fixture.cpp','ClipComposition.hpp'].map(f=>[f,{bytes:readFileSync(resolve(target,f)).length,sha256:sha(readFileSync(resolve(target,f)))}])),
  wasmSha256:sha(readFileSync(resolve(target,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(target,'gpu.mjs'))),flags,toolSha256:sha(readFileSync(import.meta.filename)),
  vertexSourceChanged:true,fragmentUVOverride:name==='uv',cpuComposition:'projection * (view * world), binary32 product and sum stored separately in k0..3 order',
  instanceComposition:'Each original 68B world/factor record gains its own 64B derived clip matrix; original world attrs4..7 and factor8 retained; clip attrs9..12; uploaded stride132; draw count uses original instanceSize/68',
  preservesFogEye:true,preservesCurrentDepth16:true,worldViewportSnap:false,worldViewportExpression:'homogeneous scaled reciprocal: scale=(extent*0.5)/clipW; screen=(clipXY+clipW)*scale; correctedClip=((screen+0.5)/extent*2-1)*clipW',transformFeedback:false,constantVaryings:false,capturedNativeClipValuesUsed:false,
  limits:'Independent diagnostic candidate. Captured original matrices/vertices enter normal fixture API; computed CPU clip matrices are not read from Native controls. Production unchanged; actual GPU/browser results must be collected before any equivalence claim.'};
 writeFileSync(resolve(target,'build.json'),JSON.stringify(build,null,2)+'\n');builds.push({name,buildSha256:sha(readFileSync(resolve(target,'build.json')))});
 console.log('Built sequential clip plus homogeneous viewport diagnostic',name,build.wasmSha256);
}
writeFileSync(resolve(out,'sources.json'),JSON.stringify({label,sourceBindings:baseSources.sourceBindings,
 snapshots:baseSources.snapshots,builds,toolSha256:sha(readFileSync(import.meta.filename)),
 scope:'Frozen current Renderer baseline plus independent derived CPU sequential clip composition. Existing eye/fog, D16, batching, strips and per-instance original model inputs remain. Independent uniform homogeneous scaled-reciprocal viewport expression, no explicit snap. No production changes or Native matrix/clip readback substitution.'},null,2)+'\n');


