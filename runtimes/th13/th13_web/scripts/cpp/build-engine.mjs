// Build the shared engine for one title. This is not a playable runtime by itself: it compiles the engine half
// (cpp/game) with that title's PORT_TITLE and links it into a wasm module, which is the first half of a per-title
// runtime and the half that tells us whether the engine really is title-portable.
//
// The engine currently lives under the th12 runtime and this script reaches it by relative path, because the
// per-title tables - the no-op table, the colliding-opcode list, the archive keys - are what differ and they are
// selected at compile time by PortTitle.hpp. When the engine is moved to a directory of its own, SHARED is the
// only line that changes.
//
// Instrument note. The first link of this module used `-Wl,--strip-all` with no exports and produced a 220-byte
// module: with no entry and nothing exported, the linker garbage-collected every function, so the artefact
// looked like a successful build while containing no engine code at all. The link therefore uses
// `-Wl,--no-gc-sections` and the script refuses to report success for a module below MIN_BYTES. A build that
// cannot contain the engine is not evidence that the engine builds.
import {spawn,spawnSync} from 'node:child_process';
import {mkdirSync,readdirSync,readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const root=fileURLToPath(new URL('../../',import.meta.url));
const titleArg=process.argv.indexOf('--title');
const title=titleArg>=0?Number(process.argv[titleArg+1]):13;
if(![12,13,14,16,17,18].includes(title))throw Error('--title must be one of 12, 13, 14, 16, 17, 18');
const SHARED=resolve(root,'../../th12/th12_web');
const sources=readdirSync(resolve(SHARED,'cpp/game')).filter(n=>n.endsWith('.cpp')).sort().map(n=>'cpp/game/'+n);
const headers=[...readdirSync(resolve(SHARED,'cpp/game')).filter(n=>/\.(hpp|inc)$/.test(n)).map(n=>'cpp/game/'+n)].sort();
const compiler=resolve(root,'../../../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');
if(!existsSync(compiler))throw Error('compiler not found at '+compiler);
const out=resolve(root,'artifacts/cpp'),objects=resolve(out,'objects-th'+title),wasm=resolve(out,`engine-th${title}.wasm`);
mkdirSync(objects,{recursive:true});
// 256 KiB. The engine's own text is far larger than this; the threshold exists to reject a module that was
// stripped down to nothing, not to measure the engine.
const MIN_BYTES=256*1024;
const compileFlags=['--target=wasm32-wasip1','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti',`-DPORT_TITLE=${title}`,'-c'];
// --no-gc-sections: keep every function, because there is no entry point and nothing is exported.
const linkFlags=['--target=wasm32-wasip1','-O2','-g0','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-Wl,--no-gc-sections'];
const hash=b=>createHash('sha256').update(b).digest('hex');
const headersKey=hash(headers.map(n=>n+' '+hash(readFileSync(resolve(SHARED,n)))).join('\n'));
const run=args=>new Promise((accept,reject)=>{const child=spawn(compiler,args,{cwd:SHARED,windowsHide:true,stdio:['ignore','pipe','pipe']});let log='';child.stdout.on('data',b=>log+=b);child.stderr.on('data',b=>log+=b);child.on('error',reject);child.on('exit',code=>code?reject(Error(log)):accept());});
let cursor=0;const compiled=new Array(sources.length);
await Promise.all(Array.from({length:4},async()=>{while(cursor<sources.length){const index=cursor++,source=sources[index],object=resolve(objects,source.replaceAll('/','_')+'.o'),key=hash(JSON.stringify([compileFlags,headersKey,hash(readFileSync(resolve(SHARED,source)))]));if(!existsSync(object)||!existsSync(object+'.key')||readFileSync(object+'.key','utf8')!==key){await run([...compileFlags,source,'-o',object]);writeFileSync(object+'.key',key);}compiled[index]=object;}}));
await run([...linkFlags,...compiled,'-o',wasm]);
const bytes=readFileSync(wasm),mod=new WebAssembly.Module(bytes);
if(bytes.length<MIN_BYTES)throw Error(`the link produced ${bytes.length} bytes, below the ${MIN_BYTES}-byte floor: with no entry point and no exports an over-eager link can keep nothing, and that is not a build of the engine`);
const compilerVersion=spawnSync(compiler,['--version'],{windowsHide:true,encoding:'utf8'}).stdout.trim();
const report={kind:'shared-engine-per-title-build',title,completeGame:false,engineSources:sources.length,sharedRoot:'runtimes/th12/th12_web',sources,compileFlags,linkFlags,compilerVersion,bytes:bytes.length,sha256:hash(bytes),imports:WebAssembly.Module.imports(mod),exports:WebAssembly.Module.exports(mod),sourceHashes:Object.fromEntries([...sources,...headers].map(s=>[s,hash(readFileSync(resolve(SHARED,s)))])),buildScriptHash:hash(readFileSync(resolve(root,'scripts/cpp/build-engine.mjs')))};
writeFileSync(resolve(out,`engine-th${title}-build.json`),JSON.stringify(report,null,2)+'\n');
console.log(`engine-th${title}.wasm ${bytes.length} bytes, ${sources.length} sources, ${WebAssembly.Module.imports(mod).length} imports`);
