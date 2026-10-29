// Validate the actual Launcher function and overlay it in the frozen preview.
// DOM/Runtime controls declare I/O; only separate browser evidence proves UI.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {stripTypeScriptTypes} from 'node:module';
import {execFileSync} from 'node:child_process';
import {runInNewContext} from 'node:vm';
import {resolve,relative,sep} from 'node:path';
const root=resolve(import.meta.dirname,'..'),args=process.argv.slice(2);
assert(args.length===4&&args[0]==='--report'&&args[2]==='--output');
const reportPath=resolve(root,args[1]),out=resolve(root,args[3]);
assert(out.startsWith(resolve(root,'artifacts/th14')+sep));mkdirSync(out);
const hash=b=>createHash('sha256').update(b).digest('hex');
const sourcePath='runtimes/th12/th12_web/launcher/src/launcher/app.mts';
const source=readFileSync(resolve(root,sourcePath),'utf8');
const base='06b8b815b5037cc65500ea219f424c6c2ba17414';
const old=execFileSync('git',['-C',resolve(root,'tools/tmp/github-source-release'),'show',base+':'+sourcePath],{encoding:'utf8'});
function bounds(text){const start=text.indexOf('async function manageReplays(');assert(start>=0&&text.indexOf('async function manageReplays(',start+1)<0);const end=text.indexOf('\n}\n',start)+2;assert(end>start);return {start,end,body:text.slice(start,end)};}
const before=bounds(old),after=bounds(source);
assert.equal(source.slice(0,after.start),old.slice(0,before.start));
assert.equal(source.slice(after.end),old.slice(before.end));
const beforeJs=stripTypeScriptTypes(before.body,{mode:'strip'}),afterJs=stripTypeScriptTypes(after.body,{mode:'strip'});
async function control(body,options){
 const events=[],state={game:options.game,ready:options.ready??false};
 const originalError=new Error(options.error??'runtime startup failure');
 const classes=new Set(),elements=new Map();
 const dialog={open:false,classList:{remove:x=>classes.delete(x)},showModal(){events.push('modal');this.open=true;}};
 const list={replaceChildren(){events.push('clear');},append(){events.push('row');}};
 const summary={textContent:''};elements.set('#replayDialog',dialog);elements.set('#replayList',list);elements.set('#replaySummary',summary);
 async function ensureRuntime(show){
  assert.equal(show,false);events.push('ensure');
  if(options.error==='startup')throw originalError;
  if(!state.ready&&dialog.open&&state.game==='th14')throw originalError;
  state.ready=true;if(options.changeGame)state.game=options.changeGame;
 }
 const context={state,$:s=>{assert(elements.has(s));return elements.get(s);},
  document:{createElement:()=>({className:'',innerHTML:'',textContent:''})},
  requestAnimationFrame:cb=>{events.push('raf');cb();},t:s=>s,ensureRuntime,
  // Declare the list operation's Runtime dependency without opening files.
  refreshReplayManager:async argument=>{assert(argument.animateRows);events.push('refresh');if(!state.ready)await ensureRuntime(false);if(options.error==='list')throw originalError;},};
 let thrown=null;try{await runInNewContext(body+'\nmanageReplays()',context);}catch(error){thrown=error;}
 return {events,open:dialog.open,ready:state.ready,game:state.game,errorSame:thrown===originalError,error:thrown?.message??null};
}
const cases=[];
for(const version of ['before','after']){
 const body=version==='before'?beforeJs:afterJs;
 for(const options of [
  {name:'th14-cold',game:'th14'},
  {name:'th14-ready',game:'th14',ready:true},
  {name:'th10-cold',game:'th10'},
  {name:'th08-cold',game:'th08'},
  {name:'th14-startup-failure',game:'th14',error:'startup'},
  {name:'th14-list-failure',game:'th14',ready:true,error:'list'},
  {name:'th14-selection-changed',game:'th14',changeGame:'th10'},
 ]){
  const result=await control(body,options);cases.push({version,name:options.name,declaredIo:true,...result});
  if(options.name==='th14-cold'){
   assert.equal(!!result.error,version==='before');
   if(version==='after')assert(result.events.indexOf('ensure')<result.events.indexOf('modal'));
  }else if(options.name==='th14-startup-failure'||options.name==='th14-list-failure')assert(result.errorSame);
  else if(options.name==='th14-selection-changed'){
   if(version==='after')assert(!result.open&&!result.events.includes('refresh'));
  }else assert.equal(result.error,null);
 }
}
for(const name of ['th14-ready','th10-cold','th08-cold','th14-list-failure']){
 const pair=cases.filter(row=>row.name===name);assert.deepEqual(pair[0].events,pair[1].events);
}
const reportRaw=readFileSync(reportPath),report=JSON.parse(reportRaw),route='assets/launcher/app.mjs';
const frozen=readFileSync(resolve(root,report.files[route].path),'utf8');assert.equal(hash(frozen),report.files[route].sha256);
const original=bounds(frozen),normalize=s=>s.replace(/\/\/[^\n]*/g,'').replace(/\s+/g,'');
assert.equal(normalize(original.body),normalize(beforeJs),'Declared source base must match frozen function');
const result=frozen.slice(0,original.start)+afterJs+frozen.slice(original.end),target=resolve(out,'app.mjs');
writeFileSync(target,result);execFileSync(process.execPath,['--check',target]);
report.files[route]={path:relative(root,target).split(sep).join('/'),bytes:Buffer.byteLength(result),sha256:hash(result)};
report.roots.push(relative(root,out).split(sep).join('/'));
report.replayManagerStartupSource={path:sourcePath,sha256:hash(source),baseCommit:base,baseSourceSha256:hash(old),actualProductionFunctionStripped:true,onlyManageReplaysChanged:true,originalFrozenFunctionMatched:true};
report.parentCandidateReport={path:relative(root,reportPath).split(sep).join('/'),sha256:hash(reportRaw)};
const proof={schema:'th14/replay-manager-startup-order-controls/1',actualFunctionSource:sourcePath,sourceSha256:hash(source),baseCommit:base,toolSha256:hash(readFileSync(new URL(import.meta.url))),declaredIoControls:cases.length,controls:cases,oldColdTh14Failed:true,currentColdTh14ControlPassed:true,nonTh14AndReadyOrderUnchanged:true,changedSelectionDoesNotOpenStaleDialog:true,canonicalSourceOnlyOneFunctionChanged:true,appSha256:hash(result),wasmSha256:report.wasmSha256,browserEvidenceRequiredSeparately:true,completeGame:false,nativeEquivalent:false};
writeFileSync(resolve(out,'controls.json'),JSON.stringify(proof,null,2)+'\n');
writeFileSync(resolve(out,'launcher-report.json'),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({declaredIoControls:cases.length,sourceSha256:hash(source),appSha256:hash(result),wasmUnchanged:report.wasmSha256,onlyManageReplaysChanged:true}));
