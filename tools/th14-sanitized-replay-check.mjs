// Independent public input through the actual production game sources with
// address/undefined-behavior instrumentation. No native oracle is generated.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
import {spawn} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),sdk=resolve(root,'runtimes/th12/tools/emsdk');
const sha=b=>createHash('sha256').update(b).digest('hex'),label=process.argv[2];assert(/^[a-z0-9-]{1,64}$/.test(label));
const out=resolve(root,'artifacts/th14/sanitized-replay',label),objects=resolve(out,'objects');mkdirSync(objects,{recursive:true});
const engine=JSON.parse(readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')));
for(const [name,digest] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,name))),digest,name);
const python=resolve(sdk,'python',readdirSync(resolve(sdk,'python')).sort().reverse().find(n=>existsSync(resolve(sdk,'python',n,'python.exe'))),'python.exe');
const env={...process.env,EM_CONFIG:resolve(sdk,'.emscripten'),EMSDK:sdk,EMSDK_PYTHON:python,EMCC_CORES:'4',TEMP:out,TMP:out,TMPDIR:out};
const flags=['-O1','-g','-std=c++17','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-fsanitize=address,undefined','-fno-sanitize-recover=all'];
const run=args=>new Promise((accept,reject)=>{const p=spawn(python,[resolve(sdk,'upstream/emscripten/emcc.py'),...args],{cwd:rt,env,windowsHide:true,stdio:['ignore','pipe','pipe']});let log='';for(const stream of [p.stdout,p.stderr])stream.on('data',b=>log+=b);p.on('error',reject);p.on('exit',code=>code?reject(Error(log)):accept());});
const compiled=[],headers=Object.fromEntries(Object.entries(engine.sourceHashes).filter(([name])=>!name.endsWith('.cpp'))),settings=JSON.stringify([flags,headers]);let cursor=0;
await Promise.all(Array.from({length:4},async()=>{while(cursor<engine.sources.length){const index=cursor++,name=engine.sources[index],object=resolve(objects,name.replaceAll('/','_')+'.o'),key=sha(settings+name+engine.sourceHashes[name]);if(!existsSync(object)||!existsSync(object+'.key')||readFileSync(object+'.key','utf8')!==key){await run([...flags,'-c',name,'-o',object]);writeFileSync(object+'.key',key);}compiled[index]=object;}}));
writeFileSync(resolve(out,'compile-build.json'),JSON.stringify({flags,sourceHashes:engine.sourceHashes,objectSha256:Object.fromEntries(compiled.map(p=>[p,sha(readFileSync(p))]))},null,2)+'\n');
const fixture='tests/cpp/th14-public-replay-physical-fixture.cpp',loader=resolve(out,'sanitized.mjs');
await run([...flags,fixture,...compiled,'--no-entry','-sDEFAULT_TO_CXX=1','-sMODULARIZE=1','-sEXPORT_ES6=1','-sENVIRONMENT=node','-sALLOW_MEMORY_GROWTH=1','-sINITIAL_MEMORY=536870912','-sMAXIMUM_MEMORY=2147483648','-sSTACK_SIZE=1048576','-sINVOKE_RUN=0','-sASSERTIONS=1','-sEXIT_RUNTIME=0','-sINCOMING_MODULE_JS_API=wasmBinary,print,printErr','-sEXPORTED_RUNTIME_METHODS=HEAPU8,HEAPU32','-o',loader]);
const wasm=readFileSync(resolve(out,'sanitized.wasm')),create=(await import(pathToFileURL(loader).href)).default,errors=[];
const module=await create({wasmBinary:wasm,print:line=>{if(line)console.log(line);},printErr:line=>{errors.push(line);console.error(line);}});
// These names are fixture export_name annotations, not hidden game probes.
const c=Object.fromEntries(['allocate','open_archive','public_replay_begin','tick','draw','public_replay_clock','phase','public_replay_status','public_replay_observations','reference_data','error'].map(name=>[name,module['_'+name]??module[name]]));
for(const [name,fn] of Object.entries(c))assert.equal(typeof fn,'function','Missing instrumented fixture export '+name);
const upload=b=>{const pointer=c.allocate(b.length);module.HEAPU8.set(b,pointer);return pointer;};
const replay=readFileSync(resolve(root,'artifacts/th14/public-replay-reference/th14_udzp05.rpy')),target=JSON.parse(readFileSync(resolve(root,'runtimes/th14/target.json'))),archive=readFileSync(target.dataArchives['th14.dat'].path);
assert.equal(c.open_archive(upload(archive),archive.length),1);assert.equal(c.public_replay_begin(upload(replay),replay.length),1);
let frames=0;
for(let frame=1;frame<=200000;frame++){
 assert.equal(c.tick(0),1,'Instrumented production tick '+frame);assert.equal(c.draw(),1,'Instrumented production draw '+frame);assert.equal(c.public_replay_clock(frame/60),1);frames=frame;
 if(frame%12000===0)console.log(JSON.stringify({instrumentedFrames:frame,stage:c.public_replay_status(0)}));
 if([3,4,5].includes(c.phase()))break;
}
assert.equal(c.phase(),4);assert.equal(c.public_replay_status(3),0);assert.equal(c.public_replay_status(5),0);assert.equal(c.public_replay_status(6),0);
assert(!errors.some(line=>/AddressSanitizer|runtime error:|UndefinedBehaviorSanitizer/.test(line)));
const result={passed:true,completeGame:false,nativeEquivalent:false,frames,stage:c.public_replay_status(0),candidatePlaybackEnded:true,gameOver:false,errors,
 sanitizerFlags:flags,sourceHashes:engine.sourceHashes,fixtureSha256:sha(readFileSync(resolve(rt,fixture))),wasmBytes:wasm.length,wasmSha256:sha(wasm),toolSha256:sha(readFileSync(import.meta.filename)),
 scope:'Production C++ gameplay with the intact independent public player recording, ordinary collision and stock, compiled with AddressSanitizer and UndefinedBehaviorSanitizer, both nonrecovering. No invulnerability/forced progression, custom inputs or native oracle generation. Only executed memory/math paths are checked; leak teardown, all characters/difficulties/Extra, original equality, physical graphics/audio/browser storage and whole-game1:1 remain separate.'};
writeFileSync(resolve(root,`docs/porting/th14-sanitized-replay-${label}-observed-oct13.json`),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:true,frames,wasmBytes:wasm.length}));
