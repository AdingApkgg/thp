// Controlled world viewport quantization; preserve the production matrix/depth path.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),base=resolve(root,'artifacts/th14/stage-current-graphics-fe406-oct14'),out=resolve(root,'artifacts/th14/stage-current-world-snap8-fe406-oct14'),sdk=resolve(root,'runtimes/th12/tools/emsdk');
const sha=b=>createHash('sha256').update(b).digest('hex');mkdirSync(out,{recursive:true});assert(!existsSync(resolve(out,'capture-complete.json')),'Completed capture is immutable');
const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp','fixture.cpp'];
const baseline=JSON.parse(readFileSync(resolve(base,'sources.json'))),reportPath='docs/porting/th14-stage-current-graphics-observed-oct14.json';
const anchor='gl_Position.xy+=gl_Position.w/viewport.zw;';
const step='vec2 worldScreen=(gl_Position.xy/gl_Position.w*0.5+vec2(0.5))*viewport.zw;worldScreen=roundEven(worldScreen*256.0)/256.0;gl_Position.xy=((worldScreen+vec2(0.5))/viewport.zw*2.0-vec2(1.0))*gl_Position.w;';
mkdirSync(resolve(out,'source'),{recursive:true});
for(const file of files){const raw=readFileSync(resolve(base,'source',file));assert.equal(sha(raw),baseline.snapshots[file]);writeFileSync(resolve(out,'source',file),raw);}
const builds=[];
for(const name of ['color','uv']){
 const target=resolve(out,name);mkdirSync(target,{recursive:true});const old=JSON.parse(readFileSync(resolve(base,name,'build.json')));
 for(const file of files){let s=readFileSync(resolve(base,name,file),'utf8');assert.equal(sha(Buffer.from(s)),old.sources[file].sha256);
  if(file==='Shaders.hpp'){assert.equal(s.split(anchor).length,2);s=s.replace(anchor,step);}
  writeFileSync(resolve(target,file),s);
 }
 const flags=old.flags;execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',[resolve(sdk,'upstream/emscripten/emcc.py'),...flags,resolve(target,'fixture.cpp'),resolve(target,'Renderer.cpp'),'-o',resolve(target,'gpu.mjs')],{cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:target,TMP:target,TMPDIR:target},stdio:'inherit',windowsHide:true});
 const build={...old,label:'Sourcefe406-current-world-snap8-oct14',vertexSourceChanged:true,worldViewportQuantizationBits:8,baselineBuildSha256:sha(readFileSync(resolve(base,name,'build.json'))),baselineReportSha256:sha(readFileSync(resolve(root,reportPath))),sources:Object.fromEntries(files.map(f=>[f,{bytes:readFileSync(resolve(target,f)).length,sha256:sha(readFileSync(resolve(target,f)))}])),wasmSha256:sha(readFileSync(resolve(target,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(target,'gpu.mjs'))),toolSha256:sha(readFileSync(import.meta.filename)),worldShaderAnchor:anchor,worldShaderReplacement:step};
 writeFileSync(resolve(target,'build.json'),JSON.stringify(build,null,2)+'\n');builds.push({name,buildSha256:sha(readFileSync(resolve(target,'build.json')))});console.log('Built isolated current world snap8',name,build.wasmSha256);
}
writeFileSync(resolve(out,'sources.json'),JSON.stringify({...baseline,label:'Sourcefe406-current-world-snap8-oct14',builds,toolSha256:sha(readFileSync(import.meta.filename)),baselineSourcesSha256:sha(readFileSync(resolve(base,'sources.json'))),baselineReportPath:reportPath,baselineReportSha256:sha(readFileSync(resolve(root,reportPath))),scope:'Diagnostic uniform snap8 world viewport step only. Original current projection*eye, renderer, EXT_clip_control and D16 retained. No production edits or per-pixel corrections.'},null,2)+'\n');
