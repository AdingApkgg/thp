// Build th13's SDL3 web harness. Same chain as th12's scripts/build-sdl.mjs, with three differences: the title
// constant is 13, the engine and the SDL platform layer are the shared ones under the th12 runtime, and the target
// description is this title's own runtimes/th13/target.json.
//
// The engine half already builds for every title (see th13_web/scripts/cpp/build-engine.mjs). What this script adds
// is the playable link: the SDL3 platform layer, the renderer, and the -sEXPORTED_FUNCTIONS C ABI the host shell
// drives. The ABI names are historical (_th11_*) and title-independent - they are the host protocol, not th12's.
//
// The SDK and the portable renderer are not copied per title. They live in the th12 workspace and are reached by
// path; duplicating a multi-hundred-megabyte emsdk for each of six titles would be the wrong trade. SHARED_SDK and
// PORTABLE are the two lines to change when the workspace layout changes.
import {spawn} from 'node:child_process';
import {readFileSync,readdirSync,mkdirSync,existsSync,writeFileSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const titleAt=process.argv.indexOf('--title');
const title=titleAt<0?13:Number(process.argv[titleAt+1]);
if(![13,14].includes(title))throw Error('--title must be 13 or 14');
const root=resolve(fileURLToPath(new URL('../',import.meta.url)),'../..',`th${title}/th${title}_web`);
const sharedRuntime=resolve(root,'../../th12/th12_web');                  // engine and SDL layer
const sharedWorkspace=resolve(root,'../../th12');                         // emsdk and portable renderer
const sdk=resolve(sharedWorkspace,'tools/emsdk');
const emcc=resolve(sdk,'upstream/emscripten/emcc.py');
const release=process.argv.includes('--release');
const target=JSON.parse(readFileSync(resolve(root,'../target.json'),'utf8'));
if(target.game!==`th${title}`)throw Error(`runtimes/th${title}/target.json says game=${target.game}`);
const out=resolve(root,process.env[`TH${title}_OUTPUT`]||(release?'artifacts/sdl3-release':'artifacts/sdl3'));
const objects=resolve(out,'objects');mkdirSync(objects,{recursive:true});
const env={...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,EMCC_CORES:'4'};
const python=(()=>{
 if(process.env.EMSDK_PYTHON&&existsSync(process.env.EMSDK_PYTHON))return process.env.EMSDK_PYTHON;
 const bundled=resolve(sdk,'python');
 if(existsSync(bundled))for(const name of readdirSync(bundled).sort().reverse()){
  const candidate=resolve(bundled,name,'python.exe');
  if(existsSync(candidate))return candidate;
 }
 return process.platform==='win32'?'python3':'python3';
})();
const common=['-O2','-g0','--profiling-funcs','-std=c++17','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DTH_NATIVE_PLATFORM=1',`-DTH11_DEVELOPMENT_HARNESS=${release?0:1}`,`-DPORT_TITLE=${title}`,'--use-port=sdl3'];
const run=args=>new Promise((resolveRun,reject)=>{const p=spawn(python,[emcc,...args],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});let log='';for(const s of [p.stdout,p.stderr])s.on('data',b=>{log+=b;process.stdout.write(b);});p.on('error',reject);p.on('exit',code=>code?reject(Error(`th${title} SDL build failed ${code}\n${log}`)):resolveRun());});
const files=dir=>readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(resolve(dir,e.name)):e.name.endsWith('.cpp')?[resolve(dir,e.name)]:[]);
const source=[...files(resolve(sharedRuntime,'cpp/game')),...files(resolve(sharedRuntime,'cpp/sdl')),resolve(sharedWorkspace,'portable/sdl/Renderer.cpp')];
const headerFiles=dir=>readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?headerFiles(resolve(dir,e.name)):/\.(h|hpp|inc)$/.test(e.name)?[resolve(dir,e.name)]:[]);
const headers=[...headerFiles(resolve(sharedRuntime,'cpp')),...headerFiles(resolve(sharedWorkspace,'portable/sdl')),...headerFiles(resolve(sharedWorkspace,'portable/input'))].sort();
const sha=b=>createHash('sha256').update(b).digest('hex');
const headerHash=sha(headers.map(p=>p+sha(readFileSync(p))).join('\n'));
const settings=JSON.stringify([common,headerHash]);
async function compile(file){const name=relative(sharedWorkspace,file).replaceAll('\\','_').replaceAll('/','_'),object=resolve(objects,name+'.o'),key=sha(settings+sha(readFileSync(file)));if(existsSync(object)&&existsSync(object+'.key')&&readFileSync(object+'.key','utf8')===key)return object;await run([...common,'-c',file,'-o',object]);writeFileSync(object+'.key',key);return object;}
const objectsBuilt=[];let cursor=0;await Promise.all(Array.from({length:4},async()=>{while(cursor<source.length){const i=cursor++;objectsBuilt[i]=await compile(source[i]);}}));
const loader=resolve(out,release?'th11.mjs':'th11-harness.mjs');
// The export list is the host protocol and is identical to th12's: same names, same harness entry points.
const exports=['_malloc','_free','_th11_validate_file','_th11_save_scores','_th11_save_replay','_th11_initialize','_th11_last_resource','_th11_music_enabled','_th11_audio_statistics','_th11_return_title','_th11_restart','_th11_error','_th11_frame','_th11_phase','_th11_pause','_th11_resume','_th11_loop_start','_th11_loop_stop','_th11_loop_pause','_th11_key','_th11_keys_clear','_th11_touch','_th11_touch_cancel','_th11_touch_options','_th11_touch_controls','_th11_touch_stick',...(release?[]:[...(title===14?['_th11_probe_platform_tick']:[]),'_th11_tick','_th11_audio_probe','_th11_audio_samples','_th11_probe_stage','_th11_probe_dialogue','_th11_text_writes','_th11_stage','_th11_stage_frame','_th11_heap_bytes','_th11_dynamic_allocs','_th11_probe_invincibility','_th11_title','_th11_input'])];
await run([...common,'--no-entry','-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker','-sALLOW_MEMORY_GROWTH=1','-sSTACK_SIZE=1048576','-sINITIAL_MEMORY=536870912','-sMAXIMUM_MEMORY=1073741824','-sFILESYSTEM=1','-lidbfs.js','-sEXPORTED_RUNTIME_METHODS=FS,IDBFS,HEAPU8,HEAP32,HEAPU32','-sINVOKE_RUN=0','-sEXIT_RUNTIME=0','-sMIN_WEBGL_VERSION=2','-sMAX_WEBGL_VERSION=2','-sGL_SUPPORT_AUTOMATIC_ENABLE_EXTENSIONS=0','-sEXPORTED_FUNCTIONS='+exports.join(','),...objectsBuilt,'-o',loader]);
const wasm=readFileSync(loader.replace('.mjs','.wasm'));
const report={kind:`th${title}-sdl3-${release?'web-release':'harness'}`,title,completeGame:target.completeGame===true,sharedRuntime:'runtimes/th12/th12_web',targetExecutable:target.executable,bytes:wasm.length,sha256:sha(wasm),headers:Object.fromEntries(headers.map(p=>[relative(sharedWorkspace,p).replaceAll('\\','/'),sha(readFileSync(p))])),sources:Object.fromEntries(source.map(p=>[relative(sharedWorkspace,p).replaceAll('\\','/'),sha(readFileSync(p))]))};
report.loaderSha256=sha(readFileSync(loader));
report.releaseProfile=release;
report.exports=WebAssembly.Module.exports(new WebAssembly.Module(wasm));
report.buildScriptSha256=sha(readFileSync(fileURLToPath(import.meta.url)));
if(release&&report.exports.some(e=>/^th11_(?:probe_|audio_probe|audio_samples|tick$)/.test(e.name)))throw Error('Release build exposes diagnostic entry points');
writeFileSync(resolve(out,'build.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({loader,bytes:wasm.length,sha256:report.sha256}));
