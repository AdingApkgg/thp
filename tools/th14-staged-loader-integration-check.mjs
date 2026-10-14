// Private integrated loader experiment; root C++ and shared objects are read-only.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve,dirname,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {spawn,execFileSync} from 'node:child_process';
import {WASI} from 'node:wasi';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const workHome=resolve(root,'artifacts/th14/staged-loader-integration-oct14'),revision=process.env.TH14_STAGED_REVISION||'',home=revision?resolve(workHome,revision):workHome,baseline=resolve(workHome,'baseline/runtimes/th12/th12_web'),privateRt=resolve(home,revision?'source/runtimes/th12/th12_web':'private/runtimes/th12/th12_web');
mkdirSync(home,{recursive:true});
const engineBytes=readFileSync(resolve(root,'runtimes/th13/th13_web/artifacts/cpp/engine-th14-build.json')),engine=JSON.parse(engineBytes);assert.equal(Object.keys(engine.sourceHashes).length,265);
function put(path,bytes,immutable=false){mkdirSync(dirname(path),{recursive:true});if(existsSync(path)){if(immutable)assert.equal(sha(readFileSync(path)),sha(bytes),path);}else writeFileSync(path,bytes);}
for(const [p,h] of Object.entries(engine.sourceHashes)){const b=readFileSync(resolve(rt,p));assert.equal(sha(b),h,p);put(resolve(baseline,p),b,true);put(resolve(privateRt,p),b);}
function copyTree(from,to,filter){for(const row of readdirSync(from,{withFileTypes:true})){const p=resolve(from,row.name),q=resolve(to,row.name);if(row.isDirectory())copyTree(p,q,filter);else if(filter(row.name))put(q,readFileSync(p));}}
copyTree(resolve(root,'runtimes/th12/portable'),resolve(home,revision?'source/runtimes/th12/portable':'private/runtimes/th12/portable'),n=>/\.(h|hpp|inc)$/.test(n));
copyTree(resolve(rt,'tests/cpp'),resolve(privateRt,'tests/cpp'),n=>/\.(h|hpp|inc|cpp)$/.test(n));
if(process.argv.includes('--prepare')){console.log(JSON.stringify({prepared:true,sourceFiles:265,privateRt}));process.exit(0);}
const compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),objects=resolve(home,'objects');mkdirSync(objects,{recursive:true});
const compileFlags=['--target=wasm32-wasip1','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14'];
const run=args=>new Promise((accept,reject)=>{const child=spawn(compiler,args,{cwd:privateRt,windowsHide:true,env:{...process.env,TEMP:objects,TMP:objects,TMPDIR:objects},stdio:['ignore','pipe','pipe']});let log='';child.stdout.on('data',b=>log+=b);child.stderr.on('data',b=>log+=b);child.on('error',reject);child.on('exit',code=>code?reject(Error(log)):accept());});
const sources=engine.sources,allHeaders=readdirSync(resolve(privateRt,'cpp/game')).filter(n=>/\.(hpp|inc)$/.test(n)).sort();
const headerKey=sha(Buffer.concat(allHeaders.map(n=>readFileSync(resolve(privateRt,'cpp/game',n))))),privateSources={};
for(const p of [...sources,...allHeaders.map(n=>'cpp/game/'+n)])privateSources[p]=sha(readFileSync(resolve(privateRt,p)));
const cachePath=resolve(home,'object-cache.json'),cache=existsSync(cachePath)?JSON.parse(readFileSync(cachePath)):{};
const compiled=new Array(sources.length);let cursor=0;
await Promise.all(Array.from({length:3},async()=>{while(cursor<sources.length){const i=cursor++,p=sources[i],o=resolve(objects,p.replaceAll('/','_')+'.o'),key=sha(Buffer.from(privateSources[p]+headerKey+JSON.stringify(compileFlags)));
 if(cache[p]!==key||!existsSync(o)){await run([...compileFlags,'-c',p,'-o',o]);cache[p]=key;}compiled[i]=o;
}}));writeFileSync(cachePath,JSON.stringify(cache,null,2)+'\n');
const fixture='tests/cpp/th14-staged-loader-integration-fixture.cpp',wasm=resolve(home,'staged-loader-integration.wasm');
await run([...compileFlags,'-mexec-model=reactor','-Wl,--no-entry','-Wl,--export-memory','-Wl,-z,stack-size=1048576',fixture,...compiled,'-o',wasm]);
console.log(JSON.stringify({privateBuildCompleted:true,sources:sources.length,wasmBytes:readFileSync(wasm).length,wasmSha256:sha(readFileSync(wasm))}));
for(const [p,h] of Object.entries(engine.sourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h,p);
writeFileSync(resolve(home,'private-build.json'),JSON.stringify({privateBuildCompleted:true,productionChanged:false,sourceFilesVerified:265,sources,privateSourceHashes:privateSources,baselineSourceHashes:engine.sourceHashes,engineManifestSha256:sha(engineBytes),fixtureSha256:sha(readFileSync(resolve(privateRt,fixture))),wasmSha256:sha(readFileSync(wasm)),objectHashes:Object.fromEntries(compiled.map(p=>[relative(root,p).replaceAll('\\','/'),sha(readFileSync(p))])),toolSha256:sha(readFileSync(import.meta.filename))},null,2)+'\n');
