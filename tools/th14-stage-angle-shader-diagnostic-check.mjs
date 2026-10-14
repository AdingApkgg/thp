import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {installStageShaderObserver} from './th14-stage-angle-shader-observer.mjs';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/stage-angle-shader-diagnostic-oct14');
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>JSON.parse(readFileSync(p)),bindings={};
function bound(path,row){const b=readFileSync(path);if(row){assert.equal(sha(b),row.sha256);if(row.bytes!=null)assert.equal(b.length,row.bytes);}bindings[path.slice(root.length+1).replaceAll('\\','/')]={bytes:b.length,sha256:sha(b)};return b;}
const manifest=read(resolve(out,'diagnostic-manifest.json'));bound(resolve(out,'diagnostic-manifest.json'));
assert(manifest.prepared&&!manifest.executed&&!manifest.observedShaders&&!manifest.productionChanged);
assert.equal(manifest.rendererFileCount,6);
for(const [name,row]of Object.entries(manifest.bindings))bound(resolve(root,name),row);
for(const [name,row]of Object.entries(manifest.getRoutes)){assert(name.startsWith('/')&&!name.includes('..'));bound(resolve(root,row.path),row);}
for(const mode of ['color','uv']){
 const current=manifest.builds[mode],prior=read(resolve(root,'artifacts/th14/stage-production-clip-no-finite-guard-oct14',mode,'build.json'));
 assert.deepEqual(current.flags,prior.flags);assert.equal(current.wasmSha256,prior.wasmSha256,'Exact prior module bytes');
 assert.equal(current.loaderSha256,prior.loaderSha256,'Exact prior loader bytes');
 for(const name of Object.keys(current.sources))bound(resolve(out,mode,name),current.sources[name]);
}
assert.deepEqual(Object.keys(manifest.postRoutes),['/capture/color/report.json','/capture/uv/report.json']);
const html=bound(resolve(out,'index.html')).toString();assert(html.includes('Run shader diagnostic')&&html.includes('/__workspace/quiet-audio.js'));
assert(!/new\s+(?:Audio|AudioContext)\s*\(|<audio\b/.test(html));
const script=html.split('<script type="module">')[1].split('</script>')[0];
writeFileSync(resolve(out,'page-syntax.mjs'),script);execFileSync(process.execPath,['--check',resolve(out,'page-syntax.mjs')],{windowsHide:true});bound(resolve(out,'page-syntax.mjs'));
let checks=0;const test=(a,b)=>{assert.deepEqual(a,b);checks++;};
async function declaredUnit(available){
 const shaders=[{type:1,source:'declared vertex source'},{type:2,source:'declared fragment source'}],program={},other={};let linked=null,errorsRead=0;
 const calls=[];const gl={VERTEX_SHADER:1,FRAGMENT_SHADER:2,SHADER_TYPE:3,COMPILE_STATUS:4,LINK_STATUS:5,CURRENT_PROGRAM:6,VENDOR:7,RENDERER:8,VERSION:9,SHADING_LANGUAGE_VERSION:10,
  getExtension(name){return name==='WEBGL_debug_shaders'&&available?{getTranslatedShaderSource:s=>'declared translation '+s.source}:null;},
  getParameter(key){return key===6?linked:'declared parameter '+key;},getContextAttributes(){return{antialias:false};},
  shaderSource(...args){calls.push(['source',...args]);return 'native source return';},
  linkProgram(...args){calls.push(['link',...args]);return 'native link return';},
  useProgram(...args){calls.push(['use',...args]);linked=args[0];return 'native use return';},
  drawArrays(...args){calls.push(['arrays',...args]);return 'native arrays return';},
  drawElements(...args){calls.push(['elements',...args]);return 'native elements return';},
  getAttachedShaders(p){assert.equal(p,program);return shaders;},getShaderParameter(s,key){return key===3?s.type:true;},
  getShaderSource:s=>s.source,getShaderInfoLog:()=>'',getProgramParameter:()=>true,getProgramInfoLog:()=>'',
  getError(){errorsRead++;return0;}};
 const contexts=[];const canvas={getContext(...args){contexts.push(args);return args[0]==='webgl2'?gl:null;}};
 const observer=installStageShaderObserver(canvas);test(canvas.getContext('2d'),null);test(canvas.getContext('webgl2',{antialias:false}),gl);
 test(contexts[1],['webgl2',{antialias:false}]);
 for(const s of shaders)test(gl.shaderSource(s,s.source,'retained-extra'),'native source return');
 test(gl.linkProgram(program,'retained-extra'),'native link return');observer.mark({frameIndex:0});
 test(gl.useProgram(program),'native use return');test(gl.drawArrays(4,0,3),'native arrays return');
 test(gl.drawElements(4,6,5123,0),'native elements return');test(gl.useProgram(null),'native use return');
 test(gl.useProgram(other),'native use return');
 const result=await observer.snapshot(),row=result.contexts[0];
 test(row.programs[0].programId,1);test(row.programEvents.at(-1).programId,2);test(row.drawCalls,2);test(errorsRead,0);
 test(row.gpu.debugShadersExtensionAvailable,available);test(row.translatedShadersObserved,available);
 test(row.programs[0].shaders[0].translatedStatus,available?'returned':'extension_unavailable');
 if(!available)test(row.programs[0].shaders[0].translatedSource,null);
 test(row.programs[0].shaders[0].submittedSource,'declared vertex source');
 test(calls[0].slice(1),[shaders[0],shaders[0].source,'retained-extra']);
 test(calls[2].slice(1),[program,'retained-extra']);
 test(result.consumesGlErrorState,false);
}
await declaredUnit(false);await declaredUnit(true);
const reportPath=resolve(root,'docs/porting/th14-stage-angle-shader-diagnostic-prepared-oct14.json');assert(!existsSync(reportPath));
const report={diagnosticSourcePrepared:true,productionChanged:false,completeGame:false,nativeEquivalent:false,
 actualBrowserExecuted:false,actualGpuShaderObserved:false,translatedShadersObserved:false,
 privateModulesCompiled:2,actualRendererFiles:6,allCompiledModuleBytesIdenticalToPrior:true,
 visibleRunPrepared:true,localQuiet:true,mount:manifest.mount,getRouteCount:Object.keys(manifest.getRoutes).length,
 postRoutes:manifest.postRoutes,oldNativeReferencesReused:true,priorResidual:manifest.originalResidual,
 declaredObserverUnitChecks:checks,declaredObserverDependencies:'Synthetic Canvas/WebGL API recorder only; no GPU/program shader observation claimed.',
 extensionUnavailableRetainedAsNegative:true,glErrorStateNotConsumed:true,
 manifestPath:'artifacts/th14/stage-angle-shader-diagnostic-oct14/diagnostic-manifest.json',manifestSha256:sha(readFileSync(resolve(out,'diagnostic-manifest.json'))),
 bindings,toolSha256:sha(readFileSync(import.meta.filename)),
 officialReferences:['https://developer.mozilla.org/en-US/docs/Web/API/WEBGL_debug_shaders','https://developer.mozilla.org/en-US/docs/Web/API/WEBGL_debug_shaders/getTranslatedShaderSource'],
 scope:'Private build/source/regular visible Run preparation only. Two modules and six current arithmetic/render source files are byte-identical to the prior current color/UV fixture. Context API observation captures real linked/uploaded shader source and program draw associations only after ROOT runs the page. No shader/snap/FMA/precision candidate, Native/D3D or full game run, browser automation/evaluate, port listener or runtime pixel equivalence claimed.'};
writeFileSync(reportPath,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({prepared:true,observedShaders:false,declaredChecks:checks,routes:report.getRouteCount,posts:Object.keys(report.postRoutes),reportSha256:sha(readFileSync(reportPath))}));
