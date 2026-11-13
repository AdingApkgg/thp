// Exercise the actual shell command/path functions at declared FS/core boundaries.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import vm from 'node:vm';
const input=process.argv[2]??'runtimes/th12/th12_web/sdl-runtime/shell.mjs';
const source=readFileSync(input,'utf8'),sha=b=>createHash('sha256').update(b).digest('hex');
const pathSource=source.slice(source.indexOf('function path(value)'),source.indexOf('async function launch()'));
const commandSource=source.slice(source.indexOf('async function command(m)'),source.indexOf('let queue=Promise.resolve();'));
assert(pathSource.startsWith('function path(value)')&&commandSource.startsWith('async function command(m)'));
const title=source.includes('/savesth14')?'th14':'th11',root='/saves'+title+'/',replay='replay/'+title+'_ud0001.rpy';
const bytes=Uint8Array.from([116,49,51,114,2,0,1,2]);
const cases=[
 {name:'live-th14-viewer-new-file',game:'th14',viewer:true,live:true,allow:true},
 {name:'live-th14-viewer-existing-file',game:'th14',viewer:true,live:true,existing:true,allow:false},
 {name:'live-normal-game',game:'th14',viewer:false,live:true,allow:false},
 {name:'live-truthy-viewer-is-not-capability',game:'th14',viewer:1,live:true,allow:false},
 {name:'live-other-title',game:'th11',viewer:true,live:true,allow:false},
 {name:'live-score-import-remains-blocked',game:'th14',viewer:true,live:true,target:'score'+title+'.dat',allow:false},
 {name:'live-config-import-remains-blocked',game:'th14',viewer:true,live:true,target:title+'.cfg',allow:false},
 {name:'live-invalid-native-replay',game:'th14',viewer:true,live:true,nativeValid:false,allow:false},
 {name:'live-invalid-motion-data',game:'th14',viewer:true,live:true,motionValid:false,allow:false},
 {name:'live-empty-file',game:'th14',viewer:true,live:true,empty:true,allow:false},
 {name:'live-traversal-rejected',game:'th14',viewer:true,live:true,target:'replay/../score'+title+'.dat',allow:false},
 {name:'not-started-import-preserved',game:'th14',viewer:false,live:false,allow:true},
];
const rows=[];
for(const test of cases){
 const target=test.target??replay,files=new Map(),calls=[],memory=new Uint8Array(1024),old=Uint8Array.from([9,8,7]);
 if(test.existing)files.set(root+target,old);
 const context={game:test.game,launched:test.live,options:{replayViewer:test.viewer},
  Module:{HEAPU8:memory,FS:{analyzePath:name=>({exists:files.has(name)}),writeFile:(name,data)=>{calls.push(['write',name]);files.set(name,Uint8Array.from(data));}}},
  core:{malloc:n=>{calls.push(['malloc',n]);return 32;},free:p=>calls.push(['free',p])},
  callCore:async(name,kind,p,n)=>{assert.equal(name,'th11_validate_file');assert.equal(kind,1);assert.deepEqual(Array.from(memory.subarray(p,p+n)),Array.from(bytes));calls.push(['validate',kind]);return test.nativeValid!==false;},
  validateMotionReplay:()=>test.motionValid!==false,sync:async populate=>{assert.equal(populate,false);calls.push(['sync']);}};
 vm.createContext(context);vm.runInContext(pathSource+'\n'+commandSource+'\nthis.execute=command;',context);
 let error=null;
 try{await context.execute({command:'write',path:target,bytes:Array.from(test.empty?[]:bytes)});}catch(e){error=String(e);}
 assert.equal(error===null,test.allow,test.name+': '+error);
 if(test.allow){assert.deepEqual(Array.from(files.get(root+target)),Array.from(bytes));assert.deepEqual(calls.map(c=>c[0]),['malloc','validate','free','write','sync']);}
 else{assert(!calls.some(c=>c[0]==='write'||c[0]==='sync'),test.name);if(test.existing)assert.deepEqual(Array.from(files.get(root+target)),Array.from(old));}
 rows.push({name:test.name,passed:true,error,calls});
}
const report={passed:true,cases:rows.length,rows,input,sourceSha256:sha(source),actualShellCommandAndPathExecuted:true,declaredBoundaries:['FS','malloc/free','native validation result','motion validation result','syncfs'],fullNativeReplayValidationAccepted:false,browserImportAccepted:false,completeGame:false};
if(process.argv[3])writeFileSync(process.argv[3],JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({passed:true,cases:rows.length,sourceSha256:report.sourceSha256}));
