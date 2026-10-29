// Overlay only ensureRuntime in the frozen TH14 Launcher for local validation.
// The original HTML, generated resources, runtime and Wasm remain hash-bound.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {stripTypeScriptTypes} from 'node:module';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {dirname,resolve,relative,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'..');
const options=process.argv.slice(2);assert(options.length===4&&options[0]==='--report'&&options[2]==='--output');
const reportPath=resolve(root,options[1]),out=resolve(root,options[3]);
assert(out.startsWith(resolve(root,'artifacts/th14')+sep));mkdirSync(out);
const sourceName='runtimes/th12/th12_web/launcher/src/launcher/app.mts';
const source=readFileSync(resolve(root,sourceName),'utf8');
const base='29e1a8ef759d1fc8c87b18882b0f074eeccb05d2';
const oldSource=execFileSync('git',['-C',resolve(root,'tools/tmp/github-source-release'),'show',base+':'+sourceName],{encoding:'utf8'});
const hash=raw=>createHash('sha256').update(raw).digest('hex');
function bounds(text){const start=text.indexOf('async function ensureRuntime(');assert(start>=0&&text.indexOf('async function ensureRuntime(',start+1)<0);const end=text.indexOf('\n}\n',start)+2;assert(end>start);return {start,end,body:text.slice(start,end)};}
const before=bounds(oldSource),after=bounds(source);
assert(source.slice(0,after.start)===oldSource.slice(0,before.start));
assert(source.slice(after.end)===oldSource.slice(before.end));
const reportRaw=readFileSync(reportPath),report=JSON.parse(reportRaw),route='assets/launcher/app.mjs';
const frozenPath=resolve(root,report.files[route].path),frozen=readFileSync(frozenPath,'utf8');
assert(hash(frozen)===report.files[route].sha256);
const original=bounds(frozen);
const normalize=text=>text.replace(/\/\*[\s\S]*?\*\//g,'').replace(/\/\/[^\n]*/g,'').replace(/\s+/g,'');
// The original function contains no URL/regexp literals with comment syntax;
// normalization only compares formatting from the already-frozen compiler.
const strippedBefore=stripTypeScriptTypes(before.body,{mode:'strip'});
assert(!/['"`]https?:/.test(strippedBefore));
assert.equal(normalize(strippedBefore),normalize(original.body),'Frozen function differs from declared source base');
const replacement=stripTypeScriptTypes(after.body,{mode:'strip'});
const result=frozen.slice(0,original.start)+replacement+frozen.slice(original.end);
const target=resolve(out,'app.mjs');writeFileSync(target,result);
execFileSync(process.execPath,['--check',target]);
report.files[route]={path:relative(root,target).split(sep).join('/'),bytes:Buffer.byteLength(result),sha256:hash(result)};
report.roots.push(relative(root,out).split(sep).join('/'));
report.launcherStartupErrorSource={path:sourceName,sha256:hash(source),legacyCommit:base,legacySha256:hash(oldSource),
  actualProductionFunctionStripped:true,onlyFunctionChanged:true,originalFrozenFunctionMatched:true};
report.toolSha256=hash(readFileSync(fileURLToPath(import.meta.url)));
report.parentCandidateReport={path:relative(root,reportPath).split(sep).join('/'),sha256:hash(reportRaw)};
writeFileSync(resolve(out,'launcher-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({prepared:true,onlyEnsureRuntimeOverlaid:true,wasmUnchanged:report.wasmSha256,appSha256:hash(result)}));
