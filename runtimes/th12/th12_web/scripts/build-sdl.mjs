import {spawn} from 'node:child_process';
import {readFileSync,readdirSync,mkdirSync,existsSync,writeFileSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';

const root=fileURLToPath(new URL('../',import.meta.url));
const workspace=resolve(root,'..');
const sdk=resolve(workspace,'tools/emsdk');
// This workspace's emsdk keeps the active SDK in `upstream/` (EMSCRIPTEN_ROOT in .emscripten).
const emcc=resolve(sdk,'upstream/emscripten/emcc.py');
const release=process.argv.includes('--release');
const target=JSON.parse(readFileSync(resolve(root,'target.json'),'utf8'));
// The title is a parameter of the one engine, not a property of the directory that carries it:
// this tree declares its own title in target.json, and --title or TH_TITLE can build another.
// The prefix of the public API is read from the sources below, so a rename cannot leave a stale
// name on the link line.
const declaredTitle=String(target.game||'');
const title=(process.argv.find(a=>a.startsWith('--title='))||'').split('=')[1]||process.env.TH_TITLE||declaredTitle;
if(!/^th\d+$/.test(title))throw Error('cannot name the title: --title=NN or a target.json with a game (got "'+title+'")');
const titleNumber=title.replace(/^th/,'');
const out=resolve(root,process.env.TH11_OUTPUT||(release?'artifacts/sdl-release':'artifacts/sdl3'));
const objects=resolve(out,'objects');mkdirSync(objects,{recursive:true});
const env={...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,EMCC_CORES:'4'};
// emcc.py needs Python 3.8+ (walrus), but a bare `python` on PATH is often an
// older interpreter. Prefer the interpreter emsdk ships with itself.
const python=(()=>{
 if(process.env.EMSDK_PYTHON&&existsSync(process.env.EMSDK_PYTHON))return process.env.EMSDK_PYTHON;
 const bundled=resolve(sdk,'python');
 if(existsSync(bundled))for(const name of readdirSync(bundled).sort().reverse()){
  const candidate=resolve(bundled,name,'python.exe');
  if(existsSync(candidate))return candidate;
 }
 return process.platform==='win32'?'python3':'python3';
})();
// `--profiling-funcs` keeps function names in the wasm name section at -O2, which
// is what lets a browser `RuntimeError: unreachable` be mapped back to a C++
// function (tools/tmp/wnames.mjs). It costs no runtime performance.
const common=[...(process.env.TH12_DELETE_GUARD?['-DTH12_DELETE_GUARD=1','-Wl,--wrap=free','-Wl,--wrap=malloc','-Wl,--wrap=calloc','-Wl,--wrap=realloc']:[]),'-DPORT_TITLE='+titleNumber,'-O2','-g0','--profiling-funcs','-std=c++17','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DTH_NATIVE_PLATFORM=1',`-DTH11_DEVELOPMENT_HARNESS=${release?0:1}`,'--use-port=sdl3'];
const run=args=>new Promise((resolveRun,reject)=>{const p=spawn(python,[emcc,...args],{cwd:root,env,windowsHide:true,stdio:['ignore','pipe','pipe']});let log='';for(const s of [p.stdout,p.stderr])s.on('data',b=>{log+=b;process.stdout.write(b);});p.on('error',reject);p.on('exit',code=>code?reject(Error('TH11 SDL build failed '+code+'\n'+log)):resolveRun());});
const files=dir=>readdirSync(resolve(root,dir),{withFileTypes:true}).flatMap(e=>e.isDirectory()?files(dir+'/'+e.name):e.name.endsWith('.cpp')?[resolve(root,dir,e.name)]:[]);
const source=[...files('cpp/game'),...files('cpp/sdl'),resolve(workspace,'portable/sdl/Renderer.cpp')];
const headerFiles=dir=>readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?headerFiles(resolve(dir,e.name)):/\.(h|hpp|inc)$/.test(e.name)?[resolve(dir,e.name)]:[]);
const headers=[...headerFiles(resolve(root,'cpp')),...headerFiles(resolve(workspace,'portable/sdl')),...headerFiles(resolve(workspace,'portable/input'))].sort();
const sha=b=>createHash('sha256').update(b).digest('hex');
const headerHash=sha(headers.map(p=>p+sha(readFileSync(p))).join('\n'));
const settings=JSON.stringify([common,headerHash]);
async function compile(file){const name=relative(workspace,file).replaceAll('\\','_').replaceAll('/','_'),object=resolve(objects,name+'.o'),key=sha(settings+sha(readFileSync(file)));if(existsSync(object)&&existsSync(object+'.key')&&readFileSync(object+'.key','utf8')===key)return object;await run([...common,'-c',file,'-o',object]);writeFileSync(object+'.key',key);return object;}
const objectsBuilt=[];let cursor=0;await Promise.all(Array.from({length:4},async()=>{while(cursor<source.length){const i=cursor++;objectsBuilt[i]=await compile(source[i]);}}));
// The public API's prefix and the membership of every name on the link line are read from the
// sources, so the link line and the C++ cannot drift apart; an anchor that has gone missing is
// named in the build log and in the report rather than silently dropped.
const anchors=new Set();
for(const p of source)for(const m of readFileSync(p,'utf8').matchAll(/EMSCRIPTEN_KEEPALIVE[^;{]*?\b(th\d+_\w+)\s*\(/g))anchors.add(m[1]);
const prefixCounts={};for(const n of anchors){const cut=n.indexOf('_');const p=n.slice(0,cut+1);prefixCounts[p]=(prefixCounts[p]||0)+1;}
const apiPrefix=Object.entries(prefixCounts).sort((a,b)=>b[1]-a[1])[0]?.[0]||'th11_';
const harnessOnly=['tick','audio_probe','audio_samples','probe_stage','probe_dialogue','text_writes','stage','stage_frame'];
const wanted=['validate_file','save_scores','save_replay','initialize','last_resource','music_enabled','audio_statistics','return_title','restart','error','frame','phase','pause','resume','loop_start','loop_stop','loop_pause','key','keys_clear','touch','touch_cancel','touch_options','touch_controls','touch_stick',...(release?[]:harnessOnly)];
const missingAnchors=wanted.filter(s=>!anchors.has(apiPrefix+s)).map(s=>apiPrefix+s);
if(missingAnchors.length)console.warn('no EMSCRIPTEN_KEEPALIVE anchor for: '+missingAnchors.join(', '));
const exportedFunctions=(process.env.TH12_DELETE_GUARD?[]:['_malloc','_free']).concat(wanted.map(s=>'_'+apiPrefix+s));
const loader=resolve(out,release?title+'.mjs':title+'-harness.mjs');
await run([...common,'--no-entry','-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=web,worker','-sALLOW_MEMORY_GROWTH=1',...(process.env.TH12_NULL_MALLOC?['-sABORTING_MALLOC=0']:[]),...(process.env.TH12_SAFE_HEAP?['-sSAFE_HEAP=1']:[]),...(process.env.TH12_MALLOC_DEBUG?['-sMALLOC=emmalloc']:[]),'-sSTACK_SIZE='+(process.env.TH12_STACK_SIZE||'1048576'),'-sINITIAL_MEMORY='+(process.env.TH12_INITIAL_MEMORY||'536870912'),'-sMAXIMUM_MEMORY=1073741824','-sFILESYSTEM=1','-lidbfs.js','-sEXPORTED_RUNTIME_METHODS=FS,IDBFS,HEAPU8,HEAP32,HEAPU32','-sINVOKE_RUN=0','-sEXIT_RUNTIME=0','-sMIN_WEBGL_VERSION=2','-sMAX_WEBGL_VERSION=2','-sGL_SUPPORT_AUTOMATIC_ENABLE_EXTENSIONS=0','-sEXPORTED_FUNCTIONS='+exportedFunctions.join(','),...objectsBuilt,'-o',loader]);
const wasm=readFileSync(loader.replace('.mjs','.wasm'));const report={kind:title+'-sdl3-'+(release?'web-release':'harness'),title,declaredTitle,portTitle:Number(titleNumber),apiPrefix,missingAnchors,exportedFunctions,completeGame:target.completeGame===true,bytes:wasm.length,sha256:sha(wasm),architecture:{loop:'cpp-fixed-60hz-bounded-catchup',input:'cpp-sdl',renderer:'cpp-gles-semantic-batched',graphicsInterface:'semantic-state-texture-matrix',vertexUpload:'web-bufferData-direct-game-batches-cached-vao',files:'sdl-io-idbfs',launcher:'eagler-touhou/1',audio:'cpp-miniaudio-vorbis-sdl3-stream',fonts:'cpp-original-baked-glyphs-argb4444'},headers:Object.fromEntries(headers.map(p=>[relative(workspace,p).replaceAll('\\','/'),sha(readFileSync(p))])),sources:Object.fromEntries(source.map(p=>[relative(workspace,p).replaceAll('\\','/'),sha(readFileSync(p))]))};writeFileSync(resolve(out,'build.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({loader,bytes:wasm.length,sha256:report.sha256}));
