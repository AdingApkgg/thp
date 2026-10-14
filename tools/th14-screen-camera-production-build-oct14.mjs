// Prepare by default. --execute compiles one camera object per backend and links.
// Every generated file is below OUT; frozen engine/SDL objects are read only.
import {spawn} from 'node:child_process';
import {readFileSync,readdirSync,existsSync,mkdirSync,writeFileSync,copyFileSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const SHARED=resolve(ROOT,'runtimes/th12/th12_web'),WORKSPACE=resolve(SHARED,'..');
const OUT=resolve(ROOT,'artifacts/th14/screen-camera-production-build-oct14');
const CAMERA='cpp/game/SceneCamera.cpp',SDL_CAMERA='th12_web/'+CAMERA;
const ENGINE=resolve(ROOT,'runtimes/th13/th13_web/artifacts/cpp');
const SDL=resolve(ROOT,'runtimes/th14/th14_web/artifacts/sdl3-release');
const SDL_SCRIPT=resolve(ROOT,'runtimes/th13/th13_web/scripts/build-sdl.mjs');
const CHECK=resolve(ROOT,'docs/porting/th14-staged-loader-current-checkpoint-oct14.json');
const CAMERA_RECEIPT=resolve(ROOT,'artifacts/th14/startup-camera-screen-correction-prepared-oct14/preparation-receipt.json');
const COMPILER=resolve(ROOT,'tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
const PYTHON='C:/Users/APKGG/AppData/Local/Programs/Python/Python314/python.exe';
const sha=b=>createHash('sha256').update(b).digest('hex');
const read=p=>readFileSync(p), hash=p=>sha(read(p));
const load=p=>JSON.parse(read(p));
const owned=p=>{const q=relative(OUT,resolve(p));assert(q&&!q.startsWith('..')&&!resolve(p).startsWith('\\'));return p;};
const pins={};
function pin(path,expected){const value=hash(path);if(expected)assert.equal(value,expected,path);pins[path]={bytes:read(path).length,sha256:value};return value;}
function write(path,value){owned(path);mkdirSync(dirname(path),{recursive:true});const bytes=Buffer.from(JSON.stringify(value,null,2)+'\n');if(existsSync(path))assert.deepEqual(read(path),bytes,path);else writeFileSync(path,bytes,{flag:'wx'});}
function copy(from,to){owned(to);mkdirSync(dirname(to),{recursive:true});if(existsSync(to))assert.equal(hash(to),hash(from),to);else copyFileSync(from,to,1);}
function stable(){for(const [p,row] of Object.entries(pins))assert.equal(hash(p),row.sha256,'Input changed: '+p);}
function sourceMap(){return Object.fromEntries(Object.keys(check.sourceHashes).map(n=>[n,hash(resolve(SHARED,n))]));}
const args=process.argv.slice(2);assert(args.every(a=>a==='--execute'),'Only --execute is supported');
const execute=args.includes('--execute');
pin(CHECK,'85ac83a9a8abd950ca4beffb4a907771e1863735fa750c5e9bc43b47caa58cb2');
pin(CAMERA_RECEIPT,'bc688eaaba634146d5eb8bcba8a7793fddf134bcbeeb86c684f6e54157dc527f');
const check=load(CHECK),camera=load(CAMERA_RECEIPT);
assert.equal(Object.keys(check.sourceHashes).length,267);assert.equal(Object.keys(check.objectHashes).length,141);
assert.equal(camera.productionFilesChanged,1);assert(camera.nonTh14OriginalBranchByteEqual&&camera.nonScreenOriginalPrefixByteEqual);
pin(camera.beforeSource.path,check.sourceHashes[CAMERA]);pin(camera.afterSource.path,camera.afterSource.sha256);
assert.equal(camera.afterSource.sha256,'6fc589bd7c47f0757f22ebb33ee2d6647a5b53543c189d802b6781d6dbe3a391');
const current=sourceMap();assert.deepEqual(Object.keys(current).filter(n=>current[n]!==check.sourceHashes[n]),[CAMERA]);
for(const [n,value] of Object.entries(current))pin(resolve(SHARED,n),value);
const oldEngineReport=resolve(ENGINE,'engine-th14-build.json');
pin(oldEngineReport,'75050d7a652d63dd7cc777925848bee85aee018729ad23f0c3aafa3ba21915c1');
const engine=load(oldEngineReport);assert.equal(engine.engineSources,141);assert.deepEqual(engine.sourceHashes,check.sourceHashes);
pin(resolve(ENGINE,'engine-th14.wasm'),engine.sha256);
const engineHeaders=Object.keys(check.sourceHashes).filter(n=>/\.(hpp|inc)$/.test(n)).sort();
const headersKey=sha(engineHeaders.map(n=>n+' '+current[n]).join('\n'));
const engineObjects=engine.sources.map(n=>({source:n,name:n.replaceAll('/','_')+'.o'}));
for(const row of engineObjects){pin(resolve(ENGINE,'objects-th14',row.name),check.objectHashes[row.source]);pin(resolve(ENGINE,'objects-th14',row.name+'.key'));assert.equal(read(resolve(ENGINE,'objects-th14',row.name+'.key')).toString(),sha(JSON.stringify([engine.compileFlags,headersKey,check.sourceHashes[row.source]])));}
pin(resolve(SDL,'build.json'),'2287ffe5ec41efb7a96b87cbc26de5568862a6ec7724d4c1aae0b47763596562');
const oldSDL=load(resolve(SDL,'build.json'));
pin(resolve(SDL,'th11.wasm'),'64b46da7c4aa1af2426d024c176e8c77b9ecae5a3da13a1eeea6c648ee82ca54');
pin(resolve(SDL,'th11.mjs'),oldSDL.loaderSha256);
pin(SDL_SCRIPT,'801275090685d585e0bd9892bad3ef3c9614e5099ec3a9cfc7176a76deeebeb4');
const common=['-O2','-g0','--profiling-funcs','-std=c++17','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DTH_NATIVE_PLATFORM=1','-DTH11_DEVELOPMENT_HARNESS=0','-DPORT_TITLE=14','--use-port=sdl3'];
const sdlHeaders=Object.keys(oldSDL.headers).map(n=>resolve(WORKSPACE,n)).sort();
for(const [n,value] of Object.entries(oldSDL.headers))pin(resolve(WORKSPACE,n),value);
const sdlSettings=JSON.stringify([common,sha(sdlHeaders.map(p=>p+hash(p)).join('\n'))]);
const sdlObjects=Object.keys(oldSDL.sources).map(n=>({source:n,name:n.replaceAll('/','_')+'.o'}));
assert.equal(sdlObjects.length,146);assert.equal(sdlHeaders.length,149);
const sdlChanges=[];
for(const row of sdlObjects){const p=resolve(WORKSPACE,row.source),value=pin(p);if(value!==oldSDL.sources[row.source])sdlChanges.push(row.source);pin(resolve(SDL,'objects',row.name));pin(resolve(SDL,'objects',row.name+'.key'));assert.equal(read(resolve(SDL,'objects',row.name+'.key')).toString(),sha(sdlSettings+oldSDL.sources[row.source]),row.source);}
assert.deepEqual(sdlChanges,[SDL_CAMERA]);
assert.equal(readdirSync(resolve(SDL,'objects')).filter(n=>n.endsWith('.o')).length,146);
const sourceOut=resolve(OUT,'source'),engineOut=resolve(OUT,'engine'),sdlOut=resolve(OUT,'sdl');
for(const n of Object.keys(current)){copy(resolve(SHARED,n),resolve(sourceOut,n));copy(n===CAMERA?camera.beforeSource.path:resolve(SHARED,n),resolve(OUT,'old-source',n));}
for(const row of engineObjects)for(const ext of ['', '.key'])copy(resolve(ENGINE,'objects-th14',row.name+ext),resolve(engineOut,'objects',row.name+ext));
for(const row of sdlObjects)for(const ext of ['', '.key'])copy(resolve(SDL,'objects',row.name+ext),resolve(sdlOut,'objects',row.name+ext));
const prep={prepared:true,compiled:false,toolSha256:hash(fileURLToPath(import.meta.url)),cameraReceipt:CAMERA_RECEIPT,cameraReceiptSha256:hash(CAMERA_RECEIPT),sourceFiles:267,sourceChanges:[CAMERA],oldSourceHashes:check.sourceHashes,newSourceHashes:current,engineObjects:141,sdlObjects:146,sdlHeaders:149,engineFlags:engine.compileFlags,engineLinkFlags:engine.linkFlags,sdlFlags:common,inputBindings:pins,outputsRoot:OUT,oldOutputsModified:false,engineAbiVerified:false,sdlAbiVerified:false,audioPlayed:false,runtimeExecuted:false};
write(resolve(OUT,'prepared.json'),prep);
if(!execute){console.log(JSON.stringify({prepared:resolve(OUT,'prepared.json'),sha256:hash(resolve(OUT,'prepared.json')),compiled:false,sourceChanges:[CAMERA]}));process.exit(0);}
assert(!existsSync(resolve(OUT,'build-result.json')),'Build already frozen');
const temp=resolve(OUT,'temp');mkdirSync(temp,{recursive:true});
const env={...process.env,EMSDK_PYTHON:PYTHON,TEMP:temp,TMP:temp,TMPDIR:temp,TH14_OUTPUT:sdlOut,EM_FROZEN_CACHE:'1'};
function run(command,args,cwd,logName){return new Promise((accept,reject)=>{const p=spawn(command,args,{cwd,env,windowsHide:true,stdio:['ignore','pipe','pipe']});let log='';for(const s of [p.stdout,p.stderr])s.on('data',b=>{log+=b;process.stdout.write(b);});p.on('error',reject);p.on('close',code=>{const path=owned(resolve(OUT,logName));writeFileSync(path,log,{flag:'wx'});code===0?accept():reject(Error('Build failed '+code+'; '+path));});});}
await run(COMPILER,[...engine.compileFlags,CAMERA,'-o',resolve(engineOut,'objects',CAMERA.replaceAll('/','_')+'.o')],sourceOut,'engine-camera-compile.log');
writeFileSync(resolve(engineOut,'objects',CAMERA.replaceAll('/','_')+'.o.key'),sha(JSON.stringify([engine.compileFlags,headersKey,current[CAMERA]])));
await run(COMPILER,[...engine.linkFlags,...engineObjects.map(r=>resolve(engineOut,'objects',r.name)),'-o',resolve(engineOut,'engine-th14.wasm')],sourceOut,'engine-link.log');
stable();await run(process.execPath,[SDL_SCRIPT,'--title','14','--release'],ROOT,'sdl-build.log');stable();
const changedEngine=engineObjects.filter(r=>hash(resolve(engineOut,'objects',r.name))!==check.objectHashes[r.source]).map(r=>r.source);
const changedSDL=sdlObjects.filter(r=>hash(resolve(sdlOut,'objects',r.name))!==pins[resolve(SDL,'objects',r.name)].sha256).map(r=>r.source);
assert.deepEqual(changedEngine,[CAMERA]);assert.deepEqual(changedSDL,[SDL_CAMERA]);
const newSDL=load(resolve(sdlOut,'build.json'));assert.equal(newSDL.releaseProfile,true);assert.equal(newSDL.title,14);
const normalized=rows=>rows.map(r=>JSON.stringify(r)).sort();
const abi=(before,after)=>{const a=new WebAssembly.Module(read(before)),b=new WebAssembly.Module(read(after));assert.deepEqual(normalized(WebAssembly.Module.imports(a)),normalized(WebAssembly.Module.imports(b)));assert.deepEqual(normalized(WebAssembly.Module.exports(a)),normalized(WebAssembly.Module.exports(b)));return{imports:WebAssembly.Module.imports(b),exports:WebAssembly.Module.exports(b),differences:0};};
const engineAbi=abi(resolve(ENGINE,'engine-th14.wasm'),resolve(engineOut,'engine-th14.wasm'));
const sdlAbi=abi(resolve(SDL,'th11.wasm'),resolve(sdlOut,'th11.wasm'));
assert(!sdlAbi.exports.some(e=>/^th11_(?:probe_|audio_probe|audio_samples|tick$)/.test(e.name)));
const produced=[];
for(const [folder,rows] of [[engineOut,engineObjects],[sdlOut,sdlObjects]])for(const row of rows)for(const ext of ['','.key']){const p=resolve(folder,'objects',row.name+ext);produced.push({path:p,bytes:read(p).length,sha256:hash(p)});}
for(const p of [resolve(engineOut,'engine-th14.wasm'),resolve(sdlOut,'th11.wasm'),resolve(sdlOut,'th11.mjs'),resolve(sdlOut,'build.json')])produced.push({path:p,bytes:read(p).length,sha256:hash(p)});
write(resolve(OUT,'build-result.json'),{compiled:true,runtimeExecuted:false,audioPlayed:false,nativeExecuted:false,productionSourceChanges:[CAMERA],sourceFiles:267,engineObjects:141,sdlObjects:146,engineObjectChanges:changedEngine,sdlObjectChanges:changedSDL,engineAbi,sdlAbi,releaseProfile:true,oldInputsStable:true,preparedSha256:hash(resolve(OUT,'prepared.json')),sourceHashes:current,outputs:produced,completeGame:false,nativeEquivalent:false});
console.log(JSON.stringify({buildResult:resolve(OUT,'build-result.json'),sha256:hash(resolve(OUT,'build-result.json')),engineAbiDifferences:0,sdlAbiDifferences:0,compiled:true,runtimeExecuted:false}));
