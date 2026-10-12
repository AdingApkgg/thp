// Independent fresh engine objects, preserving historical engine reports.
import {spawn,spawnSync} from 'node:child_process';
import {mkdirSync,readdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
const root=resolve(import.meta.dirname,'..'),rt=resolve(root,'runtimes/th12/th12_web'),out=resolve(root,'artifacts/th14/campaign-handoffs-all-oct11'),objects=resolve(out,'objects'),compiler=resolve(rt,'../tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe');mkdirSync(objects,{recursive:true});
const sources=readdirSync(resolve(rt,'cpp/game')).filter(n=>n.endsWith('.cpp')).sort().map(n=>'cpp/game/'+n),headers=readdirSync(resolve(rt,'cpp/game')).filter(n=>/\.(hpp|inc)$/.test(n)).sort().map(n=>'cpp/game/'+n);
const compileFlags=['--target=wasm32-wasip1','-std=c++17','-O2','-g0','-ffp-contract=off','-fno-strict-aliasing','-fno-exceptions','-fno-rtti','-DPORT_TITLE=14','-c'];
const linkFlags=['--target=wasm32-wasip1','-O2','-g0','-fno-exceptions','-fno-rtti','-mexec-model=reactor','-Wl,--no-entry','-Wl,-z,stack-size=1048576','-Wl,--export-memory','-Wl,--no-gc-sections'];
const run=args=>new Promise((accept,reject)=>{const child=spawn(compiler,args,{cwd:rt,windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:['ignore','pipe','pipe']});let log='';child.stdout.on('data',b=>log+=b);child.stderr.on('data',b=>log+=b);child.on('error',reject);child.on('exit',code=>code?reject(Error(log)):accept());});
let cursor=0;const compiled=new Array(sources.length);await Promise.all(Array.from({length:4},async()=>{while(cursor<sources.length){const index=cursor++,source=sources[index],object=resolve(objects,source.replaceAll('/','_')+'.o');await run([...compileFlags,source,'-o',object]);compiled[index]=object;}}));
const path=resolve(out,'engine.wasm');await run([...linkFlags,...compiled,'-o',path]);const bytes=readFileSync(path);if(bytes.length<256*1024)throw Error('empty engine');
const sha=b=>createHash('sha256').update(b).digest('hex');const report={kind:'independent-current-engine',title:14,completeGame:false,engineSources:sources.length,sources,compileFlags,linkFlags,compilerVersion:spawnSync(compiler,['--version'],{windowsHide:true,encoding:'utf8'}).stdout.trim(),bytes:bytes.length,sha256:sha(bytes),sourceHashes:Object.fromEntries([...sources,...headers].map(n=>[n,sha(readFileSync(resolve(rt,n)))])),objectHashes:Object.fromEntries(compiled.map(p=>[p,sha(readFileSync(p))])),toolSha256:sha(readFileSync(import.meta.filename))};
writeFileSync(resolve(out,'engine-build.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({built:true,title:14,sources:sources.length,bytes:bytes.length}));
