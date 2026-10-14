// Changed translation units compile into independent title directories only.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,existsSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {createHash} from 'node:crypto';
import {spawn} from 'node:child_process';
const root=resolve(import.meta.dirname,'..'),workHome=resolve(root,'artifacts/th14/staged-loader-integration-oct14'),revision=process.env.TH14_STAGED_REVISION||'',home=revision?resolve(workHome,revision):workHome,rt=resolve(home,revision?'source/runtimes/th12/th12_web':'private/runtimes/th12/th12_web'),sha=b=>createHash('sha256').update(b).digest('hex');
const compiler=resolve(root,'runtimes/th12/tools/wasi-sdk-34.0-x86_64-windows/bin/clang++.exe'),sources=['EnemyManager','GameResources','GameSessionResources','GameBattle','GameSession'].map(n=>'cpp/game/'+n+'.cpp');
const baseline=resolve(workHome,'baseline/runtimes/th12/th12_web');
function copyHeaders(from,to){mkdirSync(to,{recursive:true});for(const row of readdirSync(from,{withFileTypes:true})){const p=resolve(from,row.name),q=resolve(to,row.name);if(row.isDirectory())copyHeaders(p,q);else if(/\.(hpp|h|inc)$/.test(row.name)){const bytes=readFileSync(p);if(existsSync(q))assert.equal(sha(readFileSync(q)),sha(bytes));else writeFileSync(q,bytes);}}}
copyHeaders(resolve(home,revision?'source/runtimes/th12/portable':'private/runtimes/th12/portable'),resolve(workHome,'baseline/runtimes/th12/portable'));
const sourceHashes=Object.fromEntries(sources.map(p=>[p,sha(readFileSync(resolve(rt,p)))])),results=[];
await Promise.all([12,13,16].map(async title=>{const records=[];
 for(const source of sources)for(const [kind,sourceRoot] of [['baseline',baseline],['private',rt]]){const out=resolve(home,'title-compile','title'+title,kind);mkdirSync(out,{recursive:true});const object=resolve(out,source.replaceAll('/','_')+'.o'),flags=['--target=wasm32-wasip1',`-DPORT_TITLE=${title}`,'-std=c++17','-O2','-ffp-contract=off','-fno-exceptions','-fno-rtti','-c',source,'-o',object];
 const compile=await new Promise((accept,reject)=>{const p=spawn(compiler,flags,{cwd:sourceRoot,windowsHide:true,env:{...process.env,TEMP:out,TMP:out,TMPDIR:out},stdio:['ignore','pipe','pipe']});let log='';p.stdout.on('data',b=>log+=b);p.stderr.on('data',b=>log+=b);p.on('error',reject);p.on('exit',code=>accept({code,log}));});
 records.push({source,kind,exitCode:compile.code,diagnostics:compile.log,errorSignatures:[...compile.log.matchAll(/error: (.*)/g)].map(m=>m[1]),sourceSha256:sha(readFileSync(resolve(sourceRoot,source))),object:compile.code?null:{path:relative(root,object).replaceAll('\\','/'),sha256:sha(readFileSync(object))}});
 }const noNewFailures=sources.every(source=>{const [before,after]=records.filter(r=>r.source===source);return before.exitCode===after.exitCode&&JSON.stringify(before.errorSignatures)===JSON.stringify(after.errorSignatures);});
 assert(noNewFailures,'New private failure for title'+title);results.push({title,translationUnits:sources.length,allPrivateCompiled:records.filter(r=>r.kind==='private').every(r=>!r.exitCode),noNewFailures,records});
}));
for(const [p,h] of Object.entries(sourceHashes))assert.equal(sha(readFileSync(resolve(rt,p))),h);
const report={privateCompilePassed:results.every(r=>r.allPrivateCompiled),compileRegressionPassed:results.every(r=>r.noNewFailures),productionChanged:false,productionVerified:false,completeGame:false,sourceHashes,results:results.sort((a,b)=>a.title-b.title),toolSha256:sha(readFileSync(import.meta.filename)),scope:'Private versus immutable baseline compilation of all changed translation units for Title12/13/16. Preexisting baseline failures are retained with exact compiler error signatures, never called passes. This is a compile regression check, not full runtime, gameplay, browser or boot behavior equivalence.'};
writeFileSync(resolve(home,'other-title-compiles.json'),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({privateCompilePassed:report.privateCompilePassed,compileRegressionPassed:report.compileRegressionPassed,titles:results.map(r=>r.title),translationUnitsEach:sources.length}));
