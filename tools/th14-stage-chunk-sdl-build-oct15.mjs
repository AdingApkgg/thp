// Prepare by default; --execute rebuilds affected SDL objects and links release.
// Prior frozen objects are SHA-bound and never changed.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,copyFileSync,existsSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),workspace=resolve(rt,'..');
const base=resolve(root,'artifacts/th14/screen-camera-production-build-oct14');
const out=resolve(root,'artifacts/th14/stage-chunk-sdl-build-oct15');
const sha=b=>createHash('sha256').update(b).digest('hex'),read=p=>readFileSync(p),hash=p=>sha(read(p));
const changedSources=['th12_web/cpp/sdl/Application.cpp','th12_web/cpp/sdl/GraphicsDevice.cpp'];
const changedHeaders=['th12_web/cpp/sdl/GraphicsDevice.hpp','th12_web/cpp/sdl/StageUploadsTh14.hpp'];
const recompile=[...changedSources,'th12_web/cpp/sdl/FontDevice.cpp'];
const args=process.argv.slice(2);assert(args.every(a=>a==='--execute'));
const oldBytes=read(resolve(base,'sdl/build.json')),old=JSON.parse(oldBytes);
const resultBytes=read(resolve(base,'build-result.json')),oldResult=JSON.parse(resultBytes);
const oldFiles=Object.fromEntries(oldResult.outputs.map(r=>[resolve(r.path),r]));
assert.equal(hash(resolve(base,'sdl/th11.wasm')),old.sha256);
assert.equal(old.sha256,'3083772c3d52e981dfd5dacd37960d9bf35ffc7acf441f247422981a3b0eb7ea');
const sourceHashes=Object.fromEntries(Object.keys(old.sources).map(n=>[n,hash(resolve(workspace,n))]));
const headerHashes=Object.fromEntries(Object.keys(old.headers).map(n=>[n,hash(resolve(workspace,n))]));
assert.deepEqual(Object.keys(sourceHashes).filter(n=>sourceHashes[n]!==old.sources[n]).sort(),changedSources.slice().sort());
assert.deepEqual(Object.keys(headerHashes).filter(n=>headerHashes[n]!==old.headers[n]).sort(),changedHeaders.slice().sort());
const copy=(from,to)=>{mkdirSync(dirname(to),{recursive:true});if(existsSync(to))assert.equal(hash(from),hash(to));else copyFileSync(from,to,1);};
const write=(path,value)=>{const bytes=Buffer.from(JSON.stringify(value,null,2)+'\n');if(existsSync(path))assert.deepEqual(read(path),bytes);else writeFileSync(path,bytes,{flag:'wx'});};
mkdirSync(out,{recursive:true});
for(const n of [...Object.keys(sourceHashes),...Object.keys(headerHashes)])copy(resolve(workspace,n),resolve(out,'source',n));
const compiler='C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';
const sdk=resolve(workspace,'tools/emsdk'),emcc=resolve(sdk,'upstream/emscripten/emcc.py');
const flags=['-O2','-g0','--profiling-funcs','-std=c++17','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DTH_NATIVE_PLATFORM=1','-DTH11_DEVELOPMENT_HARNESS=0','-DPORT_TITLE=14','--use-port=sdl3'];
const objectRows=Object.keys(sourceHashes).map(n=>{const name=n.replaceAll('/','_')+'.o',from=resolve(base,'sdl/objects',name);assert.equal(hash(from),oldFiles[from].sha256);return {source:n,name,previousSha256:hash(from),recompile:recompile.includes(n)};});
const plan={sourceHashes,headerHashes,recompile,changedSources,changedHeaders,flags,objects:objectRows,baseBuildSha256:sha(oldBytes),baseResultSha256:sha(resultBytes),toolSha256:hash(import.meta.filename),cpuOnlyVerification:true,actualAudioPlayed:false};
write(resolve(out,'plan.json'),plan);
if(!args.includes('--execute')){console.log(JSON.stringify({prepared:true,compile:false,recompile}));process.exit(0);}
assert(!existsSync(resolve(out,'build.json')),'Completed build is immutable');
const objects=resolve(out,'objects');mkdirSync(objects,{recursive:true});
const env={...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,EMCC_CORES:'3',TEMP:objects,TMP:objects,TMPDIR:objects};
const run=args=>new Promise((accept,reject)=>{const p=spawn(compiler,[emcc,...args],{cwd:resolve(out,'source/th12_web'),env,windowsHide:true,stdio:['ignore','pipe','pipe']});let log='';for(const s of[p.stdout,p.stderr])s.on('data',b=>{log+=b;process.stdout.write(b);});p.on('error',reject);p.on('exit',c=>c?reject(Error(log)):accept());});
const objectPaths=[];
for(const row of objectRows){const target=resolve(objects,row.name);if(row.recompile)await run([...flags,'-c',resolve(out,'source',row.source),'-o',target]);else copy(resolve(base,'sdl/objects',row.name),target);objectPaths.push(target);}
const exported=['_malloc','_free',...['validate_file','save_scores','save_replay','initialize','last_resource','music_enabled','audio_statistics','return_title','restart','error','frame','phase','pause','resume','loop_start','loop_stop','loop_pause','key','keys_clear','touch','touch_cancel','touch_options','touch_controls','touch_stick'].map(n=>'_th11_'+n)];
const loader=resolve(out,'th11.mjs');
await run([...flags,'--no-entry','-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker','-sALLOW_MEMORY_GROWTH=1','-sSTACK_SIZE=1048576','-sINITIAL_MEMORY=536870912','-sMAXIMUM_MEMORY=1073741824','-sFILESYSTEM=1','-lidbfs.js','-sEXPORTED_RUNTIME_METHODS=FS,IDBFS,HEAPU8,HEAP32,HEAPU32','-sINVOKE_RUN=0','-sEXIT_RUNTIME=0','-sMIN_WEBGL_VERSION=2','-sMAX_WEBGL_VERSION=2','-sGL_SUPPORT_AUTOMATIC_ENABLE_EXTENSIONS=0','-sEXPORTED_FUNCTIONS='+exported.join(','),...objectPaths,'-o',loader]);
// Compile the shared SDL graphics source for adjacent active title branches.
for(const title of [13,16])await run([...flags.filter(f=>f!=='-DPORT_TITLE=14'),'-DPORT_TITLE='+title,'-c',resolve(out,'source/th12_web/cpp/sdl/GraphicsDevice.cpp'),'-o',resolve(objects,'GraphicsDevice-th'+title+'.o')]);
for(const [n,value] of Object.entries({...sourceHashes,...headerHashes}))assert.equal(hash(resolve(workspace,n)),value,n);
const wasm=read(resolve(out,'th11.wasm')),module=new WebAssembly.Module(wasm),before=new WebAssembly.Module(read(resolve(base,'sdl/th11.wasm')));
assert.deepEqual(WebAssembly.Module.exports(module),WebAssembly.Module.exports(before));
assert.deepEqual(WebAssembly.Module.imports(module),WebAssembly.Module.imports(before));
const report={compiled:true,releaseProfile:true,title:14,completeGame:false,nativeEquivalent:false,runtimeExecuted:false,actualAudioPlayed:false,sourceHashes,headerHashes,recompiledSources:recompile,adjacentGraphicsTitlesCompiled:[13,16],objectHashes:Object.fromEntries(objectPaths.map(p=>[relative(out,p).replaceAll('\\','/'),hash(p)])),planSha256:hash(resolve(out,'plan.json')),wasmBytes:wasm.length,wasmSha256:sha(wasm),loaderSha256:hash(loader),exportsUnchanged:true,importsUnchanged:true,scope:'Three affected SDL translation units rebuilt from frozen current sources; all remaining 143 prior objects bound by full SHA and unchanged sources/headers except the two headers used by these three units. GraphicsDevice compiled for TH13 and TH16. Release module interface compared without executing game, audio or GPU.'};
write(resolve(out,'build.json'),report);console.log(JSON.stringify({compiled:true,wasmBytes:wasm.length,wasmSha256:report.wasmSha256,adjacentGraphicsTitlesCompiled:report.adjacentGraphicsTitlesCompiled}));
