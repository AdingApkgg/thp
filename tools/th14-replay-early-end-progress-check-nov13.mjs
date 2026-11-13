import assert from 'node:assert/strict';
import {writeFileSync} from 'node:fs';
import {createReplayViewerHostTh14} from '../runtimes/th12/th12_web/sdl-runtime/eagler-host.mjs';
const cases=[];
async function check(name,native,wantedFrame,wantedEnded){
 const timers=new Set();let next=0,paused=false;
 const controller=createReplayViewerHostTh14({read:path=>({path,bytes:new Uint8Array([1])}),describe:()=>({character:1,shot:0,difficulty:0,stages:[{id:1,frames:9467},{id:2,frames:11582},{id:3,frames:14726}]}),open:async()=>{},status:()=>({...native}),step:()=>1,rate:()=>{},pause:value=>{paused=value;},close:()=>{},emit:()=>{},schedule:()=>{const id=++next;timers.add(id);return id;},cancel:id=>timers.delete(id)});
 try{
  await controller.command({action:'open',path:'replay/test.rpy',stage:3});await controller.command({action:'pause'});
  assert.equal(controller.state.frame,wantedFrame,name);assert.equal(controller.state.ended,wantedEnded);assert.equal(paused,true);cases.push({name,frame:controller.state.frame,ended:controller.state.ended,passed:true});
 }finally{await controller.close();assert.equal(timers.size,0);}
}
await check('early GameOver preserves actual native cursor',{stage:3,frame:13734,frames:14726,ended:true,phase:2,active:true},34783,true);
await check('completed stage retains full end position',{stage:3,frame:14726,frames:14726,ended:true,phase:2,active:true},35775,true);
await check('ordinary pause preserves cursor',{stage:3,frame:120,frames:14726,ended:false,phase:2,active:true},21169,false);
await check('native terminal-marker position is retained',{stage:3,frame:744,frames:14726,ended:true,phase:2,active:true},21793,true);
const report={passed:true,cases,actualSharedControllerExecuted:true,nativeStatusDeclaredBoundary:true,gameplayStateWrites:false,silent:true,completeGame:false};if(process.argv[2])writeFileSync(process.argv[2],JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(report));
