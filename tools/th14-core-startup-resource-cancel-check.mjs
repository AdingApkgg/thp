// Evaluate the complete shell and call its real resource-install wrapper.
// Module initialization is intentionally pending; fetch and FS are declared ports.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {runInNewContext} from 'node:vm';
const [shellPath,hostPath,out]=process.argv.slice(2),source=readFileSync(shellPath,'utf8'),host=await import(pathToFileURL(hostPath));
const rows=[],bytes=new Uint8Array(16),base='http://localhost/runtime/th14/th14.html';
for(const [name,game,mode,expected] of [['normal','th14','normal',{writes:1,aborted:false}],['departed','th14','departed',{writes:0,aborted:true}],['body-finishes-after-departure','th14','late',{writes:0,aborted:true}],['bfcache-return-then-departure','th14','cache',{writes:1,aborted:true}],['other-title-unchanged','th11','departed',{writes:1,aborted:false}]]){
 const window=new EventTarget(),document=new EventTarget(),canvas=new EventTarget(),calls={fetch:0,writes:[],signals:[]};document.querySelector=s=>s==='canvas'?canvas:null;document.hidden=false;window.postMessage=()=>{};
 let releaseBody,bodyReached;const bodyReady=new Promise(r=>bodyReached=r);
 const fetcher=async(url,options)=>{calls.fetch++;calls.signals.push(options?.signal);return {ok:true,async arrayBuffer(){if(mode==='late'){bodyReached();return new Promise(r=>releaseBody=()=>r(bytes.buffer));}return bytes.buffer;}};};
 const code=source.replace(/^import .*;\r?\n/gm,'').replace(/game='th(?:11|14)'/,"game='"+game+"'").replace('const initialized=(async()=>{',"globalThis.fixtureEntry={installResources,bindModule:m=>{Module=m;}};\nconst initialized=(async()=>{");
 const context={window,document,location:{search:'?game='+game,origin:'http://localhost',href:base},parent:window,URLSearchParams,AbortController,console,performance,Uint8Array,Int32Array,TextDecoder,URL,createBrowserKeyboard:()=>({clear(){},event(){}}),bindOutsideTouches:()=>()=>{},runtimeEpochContract:()=>({fields:{},accepts(){return true;}}),scanCodes:{},createModule:()=>new Promise(()=>{}),setInterval:()=>0,navigator:{userAgent:'Chrome fixture',platform:'Linux',maxTouchPoints:0},crossOriginIsolated:true,
 installHostResources:(m,r,o)=>host.installResources(m,r,{...o,base,fetcher})};
 runInNewContext(code,context,{filename:shellPath,timeout:1000});context.fixtureEntry.bindModule({FS:{mkdirTree(){},writeFile(path){calls.writes.push(path);}}});
 const event=(type,persisted)=>{const e=new Event(type);Object.defineProperty(e,'persisted',{value:persisted});window.dispatchEvent(e);};
 const install=()=>context.fixtureEntry.installResources([{path:'/fonts/test.bin',url:'./font.bin',bytes:16}]);let error=null;
 try{if(mode==='departed')event('pagehide',false);if(mode==='cache'){event('pagehide',true);event('pageshow',true);await install();event('pagehide',false);}const pending=install();if(mode==='late'){await bodyReady;event('pagehide',false);releaseBody();}await pending;}catch(e){error={name:e.name,message:e.message};}
 const actual={writes:calls.writes.length,aborted:error?.name==='AbortError'},passed=JSON.stringify(actual)===JSON.stringify(expected)&&(!error||error.name==='AbortError');rows.push({name,game,passed,actual,expected,fetches:calls.fetch,signalProvided:calls.signals.map(s=>!!s),error});
}
const q={passed:rows.every(r=>r.passed),cases:rows.length,failedCases:rows.filter(r=>!r.passed).length,rows,completeShellEvaluated:true,actualInstallWrapperAndHostModule:true,moduleFactoryPending:true,controlledModuleFetchAndFilesystem:true,actualBrowserAccepted:false,completeGame:false,shellSha256:createHash('sha256').update(source).digest('hex'),hostSha256:createHash('sha256').update(readFileSync(hostPath)).digest('hex')};writeFileSync(out,JSON.stringify(q,null,2)+'\n');console.log(JSON.stringify({passed:q.passed,cases:q.cases,failedCases:q.failedCases}));process.exitCode=q.passed?0:1;
