import assert from 'node:assert/strict';
import {readFileSync, writeFileSync, mkdirSync, existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),out=resolve(root,'artifacts/th14/stage-angle-shader-diagnostic-oct14');
const parent=resolve(root,'artifacts/th14/stage-production-clip-no-finite-guard-oct14');
const base=resolve(root,'artifacts/th14/stage-gpu-stream-replay');
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>JSON.parse(readFileSync(p));
assert(!existsSync(out),'New artifact only');mkdirSync(out,{recursive:true});
const current=read(resolve(root,'docs/porting/th14-stage-production-clip-current-source-verified-oct14.json'));
assert(current.currentProductionSourceVerified&&current.color.differentChannels===880&&current.uv.allNativeFullCaseWordDifferences===5292);
const files=['Renderer.cpp','Renderer.hpp','GraphicsState.hpp','Shaders.hpp','AlphaConversion.hpp','ResampleShader.hpp'];
const bindings={},getRoutes={},sourceBindings={};
function bind(path,expected){const b=readFileSync(path),key=path.startsWith(root)?path.slice(root.length+1).replaceAll('\\','/'):path;
 const row={bytes:b.length,sha256:sha(b)};if(expected){assert.equal(row.sha256,expected.sha256,path);if(expected.bytes!=null)assert.equal(row.bytes,expected.bytes,path);}bindings[key]=row;return b;}
function put(path,bytes){mkdirSync(resolve(path,'..'),{recursive:true});writeFileSync(path,bytes);return bind(path);}
function route(name,path,expected){const bytes=bind(path,expected);getRoutes[name]={path:path.slice(root.length+1).replaceAll('\\','/'),bytes:bytes.length,sha256:sha(bytes)};}
for(const f of files){const p=resolve(root,'runtimes/th12/portable/sdl',f);sourceBindings[f]=current.sourceBindings['runtimes/th12/portable/sdl/'+f];bind(p,sourceBindings[f]);}
const sdk=resolve(root,'runtimes/th12/tools/emsdk'),builds={};
for(const mode of ['color','uv']){
 const target=resolve(out,mode);mkdirSync(target,{recursive:true});const old=read(resolve(parent,mode,'build.json'));
 bind(resolve(parent,mode,'build.json'));
 for(const f of [...files,'fixture.cpp']){
  const b=bind(resolve(parent,mode,f),old.sources[f]);
  if(f!=='fixture.cpp'){
   const actual=bind(resolve(root,'runtimes/th12/portable/sdl',f),sourceBindings[f]);
   assert.deepEqual(b,mode==='uv'&&f==='Shaders.hpp'?Buffer.from(actual.toString().replace('outColor=c;','outColor=vec4(vUV,0.0,1.0);')):actual);
  }
  put(resolve(target,f),b);
 }
 const flags=old.flags;assert(flags.includes('-O2')&&flags.includes('-ffp-contract=off')&&flags.includes('-DPORT_TITLE=14'));
 execFileSync(process.env.EMSDK_PYTHON||'C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe',
  [resolve(sdk,'upstream/emscripten/emcc.py'),...flags,resolve(target,'fixture.cpp'),resolve(target,'Renderer.cpp'),'-o',resolve(target,'gpu.mjs')],
  {cwd:root,env:{...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,TEMP:target,TMP:target,TMPDIR:target},stdio:'inherit',windowsHide:true});
 const build={diagnosticOnly:true,completeGame:false,nativeEquivalent:false,name:mode,label:'Current-shader-backend-observer-oct14',
  parentBuildSha256:sha(readFileSync(resolve(parent,mode,'build.json'))),sourceBindings:current.sourceBindings,
  sources:Object.fromEntries([...files,'fixture.cpp'].map(f=>[f,{bytes:readFileSync(resolve(target,f)).length,sha256:sha(readFileSync(resolve(target,f)))}])),
  flags,wasmSha256:sha(readFileSync(resolve(target,'gpu.wasm'))),loaderSha256:sha(readFileSync(resolve(target,'gpu.mjs'))),
  vertexSourceChanged:false,fragmentUVOverride:mode==='uv',observer:'Frontend actual-context API observer only; no CPP/GLSL substitutions'};
 put(resolve(target,'build.json'),JSON.stringify(build,null,2)+'\n');builds[mode]=build;
 for(const f of ['build.json','gpu.mjs','gpu.wasm'])route('/'+mode+'/'+f,resolve(target,f));
}
const prepared=read(resolve(base,'prepared.json'));
route('/prepared.json',resolve(base,'prepared.json'));route('/native-color.json',resolve(base,'native.json'));route('/native-color.bgra',resolve(base,'native.bgra'));
for(const t of prepared.textures)route('/'+t.file,resolve(base,t.file),{sha256:t.sha256});
const cases=read(resolve(parent,'uv-cases.json'));bind(resolve(parent,'uv-cases.json'));
const fullByKey=new Map();
for(const row of cases.fullBindings){const p=resolve(root,row.path),all=bind(p);const bytes=all.subarray(row.offset,row.offset+row.bytes);assert.equal(sha(bytes),row.sha256);fullByKey.set(row.key,bytes);}
const residual=resolve(root,'artifacts/th14/stage-current-residual-native-uv-fe406-oct14'),nr=read(resolve(residual,'native.json'));bind(resolve(residual,'native.json'));
for(let i=0;i<nr.frames.length;i++){const row=nr.frames[i],bytes=bind(resolve(residual,`frame-${String(i).padStart(3,'0')}.rgba32f`),{sha256:row.fullFloatFrameSha256});fullByKey.set([row.stage,row.frame,row.originalDrawIndex].join('/'),bytes);}
for(const row of cases.cases){const bytes=fullByKey.get([row.stage,row.frame,row.originalDrawIndex].join('/'));row.nativeFullBytesAvailable=!!bytes;if(bytes){assert.equal(sha(bytes),row.nativeSha256);const path=resolve(out,'native-full',String(row.index).padStart(3,'0')+'.rgba32f');put(path,bytes);route('/native-full/'+String(row.index).padStart(3,'0'),path);}}
assert.equal(cases.cases.filter(c=>c.nativeFullBytesAvailable).length,7);
put(resolve(out,'uv-cases.json'),JSON.stringify(cases,null,2)+'\n');route('/uv-cases.json',resolve(out,'uv-cases.json'));
const mount='/checks/stage-angle-shaders/';
const observer=bind(resolve(root,'tools/th14-stage-angle-shader-observer.mjs'));put(resolve(out,'observer.mjs'),observer);route('/observer.mjs',resolve(out,'observer.mjs'));
let html=bind(resolve(root,'tools/th14-stage-production-clip-no-finite-guard.html')).toString();
function replaceOnce(a,b){assert.equal(html.split(a).length,2,a);html=html.replace(a,b);}
replaceOnce('<button id="run">Run selected comparison</button>','<label>Mode <select id="mode"><option value="color">Color21</option><option value="uv">UV23 / Native full7</option></select></label> <button id="run">Run shader diagnostic</button>');
replaceOnce("const mode=new URL(location.href).searchParams.get('mode')||'color';if(!['color','uv'].includes(mode))throw Error('Unknown mode');","let mode='color';");
replaceOnce('<script type="module">',`<script src="/__workspace/quiet-audio.js"></script><script type="module">\nimport{installStageShaderObserver}from'${mount}observer.mjs';`);
replaceOnce("document.querySelector('#run').onclick=async()=>{document.querySelector('#run').disabled=true;try{", "document.querySelector('#run').onclick=async()=>{document.querySelector('#run').disabled=true;mode=document.querySelector('#mode').value;document.querySelector('#mode').disabled=true;const observer=installStageShaderObserver(document.querySelector('#canvas'));try{");
replaceOnce("const row=rows[i],frame=prepared.frames.find", "observer.mark({mode,frameIndex:i});const row=rows[i],frame=prepared.frames.find");
const pixelSave="const filename='frame-'+String(i).padStart(3,'0')+(mode==='color'?'.bgra':'.rgba32f'),saved=await fetch('/capture/'+mode+'/'+filename,{method:'POST',body:actual}).then(r=>{check(r.ok,'Save full pixels');return r.json();});check(saved.sha256===actualSha,'Saved pixel binding');report.savedFile=filename;reports.push(report);";
replaceOnce(pixelSave,"report.savedFile=null;report.fullPixelsArchived=false;reports.push(report);");
replaceOnce("const saved=await fetch('/capture/'+mode+'/report.json'", "report.shaderBackend=await observer.snapshot();report.fullPixelsArchived=false;report.shaderObserverSha256='"+sha(observer)+"';report.scope+=' Actual linked shader sources/translated sources and backend API queries are diagnostic observations only; full pixels are read for existing controls but not newly archived.';const saved=await fetch('/capture/'+mode+'/report.json'");
html=html.replace(/((?:fetch|import)\(\s*['"])\/(?!\/)/g,'$1'+mount).replace(/(locateFile\s*:\s*n\s*=>\s*['"])\/(?!\/)/g,'$1'+mount);
html=html.replace('Current graphics evidence</h1>','Actual linked shader/backend diagnostic</h1>');
html=html.replace('complete Native pixels available for 4 controls only','complete Native pixels available for 7 controls');
put(resolve(out,'index.html'),html);route('/',resolve(out,'index.html'));
const manifest={prepared:true,executed:false,observedShaders:false,productionChanged:false,completeGame:false,nativeEquivalent:false,
 mount,getRoutes,postRoutes:{'/capture/color/report.json':{path:'artifacts/th14/stage-angle-shader-diagnostic-oct14/capture/color-report.json',mode:'color',frames:21,maxBytes:2000000},
 '/capture/uv/report.json':{path:'artifacts/th14/stage-angle-shader-diagnostic-oct14/capture/uv-report.json',mode:'uv',frames:23,maxBytes:2000000}},
 builds,sourceBindings,rendererFileCount:6,originalReferencesReused:true,allArithmeticSourcesUnchanged:true,
 shaderObserverSha256:sha(observer),quietScriptSha256:sha(bind(resolve(root,'tools/th14-local-quiet-audio.js'))),
 originalResidual:{colorFrames:21,colorDifferentChannels:880,nativeFullUvCases:7,failedFloatWords:5292},
 bindings,toolSha256:sha(readFileSync(import.meta.filename)),
 scope:'Private current color/UV modules with exact prior fixture and6 current renderer files, same flags. The frontend observes actual shaderSource/linkProgram/useProgram/draw through its own visible Run. No browser/GL execution, Native/D3D or port session is started by this builder; no default translated shader is invented when extension unavailable.'};
put(resolve(out,'diagnostic-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
console.log(JSON.stringify({prepared:true,observedShaders:false,mount,files:Object.keys(getRoutes).length,postPaths:Object.keys(manifest.postRoutes),colorWasm:builds.color.wasmSha256,uvWasm:builds.uv.wasmSha256}));
