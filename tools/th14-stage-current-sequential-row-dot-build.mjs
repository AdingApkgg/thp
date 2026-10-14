// One isolated hypothesis: explicit row dot instead of GLSL mat4 * vec4.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),prior=resolve(root,'artifacts/th14/stage-current-sequential-clip-scaled-bias-fe406-oct14');
const out=resolve(root,'artifacts/th14/stage-current-sequential-row-dot-fe406-oct14'),sdk=resolve(root,'runtimes/th12/tools/emsdk');
const sha=b=>createHash('sha256').update(b).digest('hex'),label='Sourcefe406-sequential-row-dot-diagnostic-oct14';
mkdirSync(out,{recursive:true});assert(!existsSync(resolve(out,'capture-complete.json')),'Completed candidate is immutable');
const sources=JSON.parse(readFileSync(resolve(prior,'sources.json'))),snapshot=resolve(out,'source');mkdirSync(snapshot,{recursive:true});
for(const [file,hash] of Object.entries(sources.snapshots)){const bytes=readFileSync(resolve(prior,'source',file));assert.equal(sha(bytes),hash);writeFileSync(resolve(snapshot,file),bytes);}
const oldExpression='gl_Position=composed*vec4(position.xyz,1.0);';
const rowExpression='vec4 position4=vec4(position.xyz,1.0);gl_Position=vec4('+Array.from({length:4},(_,row)=>'dot(vec4('+Array.from({length:4},(_,col)=>'composed['+col+']['+row+']').join(',')+'),position4)').join(',')+');';
const builds=[];
for(const name of ['color','uv']){
 const before=JSON.parse(readFileSync(resolve(prior,name,'build.json'))),target=resolve(out,name);mkdirSync(target,{recursive:true});
 assert(before.flags.includes('-O2')&&!before.flags.includes('-O3'));
 for(const [file,binding] of Object.entries(before.sources)){
  let bytes=readFileSync(resolve(prior,name,file));assert.equal(sha(bytes),binding.sha256);assert.equal(bytes.length,binding.bytes);
  if(file==='Shaders.hpp'){
   let source=bytes.toString();assert.equal(source.split(oldExpression).length,2);source=source.replace(oldExpression,rowExpression);
   assert(!source.includes('isnan')&&!source.includes('isinf'),'Use prior no-finite-branch shader');
   assert(source.includes('gl_Position.xy=(gl_Position.xy*viewport.zw+vec2(gl_Position.w))/viewport.zw;'));
   assert(source.includes('vec4 eye=view*model*vec4(position.xyz,1.0);'));
   bytes=Buffer.from(source);
  }
  writeFileSync(resolve(target,file),bytes);
 }
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...before.flags,resolve(target,'fixture.cpp'),resolve(target,'Renderer.cpp'),'-o',resolve(target,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:target,TMP:target,TMPDIR:target},stdio:'inherit',windowsHide:true});
 const build={...before,label,toolSha256:sha(readFileSync(import.meta.filename)),
  sources:Object.fromEntries(Object.keys(before.sources).map(file=>{const bytes=readFileSync(resolve(target,file));return [file,{bytes:bytes.length,sha256:sha(bytes)}];})),
  wasmSha256:sha(readFileSync(resolve(target,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(target,'gpu.mjs'))),
  parentBuildSha256:sha(readFileSync(resolve(prior,name,'build.json'))),matrixVectorExpression:'Explicit vec4(dot(row0,position4),dot(row1,position4),dot(row2,position4),dot(row3,position4))',matrixVectorSourceDelta:{oldExpression,rowExpression},
  limits:'One isolated row-dot shader hypothesis from the frozen O2 sequential/scaled-bias candidate. Every other shader byte, derived CPU matrix, original instance/world/fog/D16/viewport path and compiler flag is unchanged. No Native/fitted clip injection, snapping or production source changes.'};
 writeFileSync(resolve(target,'build.json'),JSON.stringify(build,null,2)+'\n');builds.push({name,buildSha256:sha(readFileSync(resolve(target,'build.json')))});
 console.log('Built isolated row-dot diagnostic',name,build.wasmSha256);
}
writeFileSync(resolve(out,'sources.json'),JSON.stringify({...sources,label,builds,toolSha256:sha(readFileSync(import.meta.filename)),parentSourcesSha256:sha(readFileSync(resolve(prior,'sources.json'))),scope:'One independent explicit row-dot shader hypothesis. Original frozen source snapshots and all normal original-input CPU composition/instance paths retained. Only composed*position becomes four explicit row dot calls; no production changes.'},null,2)+'\n');
