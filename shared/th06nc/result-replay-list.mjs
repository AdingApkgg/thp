import {queueSound} from './sound-queue.mjs';
import {initializeResultReplayList,loadResultReplayHeaders} from './result-replay-list-init.mjs';
function interruptAll(v,id){for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,id,true);}
export function initializeReplayNameCursor({bytes,v}){
 let length=0;while(length<8&&bytes[0x9e88+length])length++;while(length>0&&bytes[0x9e88+length-1]===32)length--;v.setInt32(0x9e7c,length,true);v.setInt32(0,length>0?95:0,true);
}
function editName(state){const {v}=state;interruptAll(v,15);v.setInt16(0x19fa+(v.getInt32(0x4438,true)%15)*288,14,true);v.setInt32(0x9e94,13,true);initializeReplayNameCursor(state);}
// State12, 71b7c..72175. File headers and local calendar date are service inputs.
export function advanceResultReplayList(state,{held=0,previous=0,repeat=0,soundSlots=[-1,-1,-1],soundDisabled=false,ensureDirectory=null,readHeader=null,date='00/00/00',recordHeader=null}={}){
 const {v,bytes}=state,clock=v.getInt32(0x4450,true),edge=bit=>(held&bit)!==0&&(held&bit)!==(previous&bit),pressed=bit=>(held&bit)!==0&&(edge(bit)||repeat!==0),sound=id=>queueSound(soundSlots,id,{disabled:soundDisabled});
 if(v.getInt32(0x9e94,true)!==12)throw Error('TH06nc result: replay list state required');if(clock===0)loadResultReplayHeaders(state,{ensureDirectory,readHeader});if(clock<20)return;
 let selected=v.getInt32(0x9e7c,true);if(pressed(16)){selected--;if(selected<0)selected+=60;sound(12);}if(pressed(32)){selected++;if(selected>=60)selected-=60;sound(12);}
 if(pressed(64)){selected=(selected+45)%60;sound(12);}if(pressed(128)){selected=(selected+15)%60;sound(12);}v.setInt32(0x9e7c,selected,true);v.setInt32(0x4438,selected,true);
 if(edge(256)){
  sound(10);v.setInt32(0x4450,0,true);if(typeof date!=='string'||date.length!==8||!/^[0-9]{2}\/[0-9]{2}\/[0-9]{2}$/.test(date))throw Error('TH06nc replay: local date required');bytes.set([...date].map(c=>c.charCodeAt(0)),0xbae4);bytes[0xbaec]=0;
  if(recordHeader){bytes[0xbad6]=recordHeader[6];bytes[0xbad8]=recordHeader[8];}
  const p=0x9eb0+selected*120;if(v.getUint32(p,true)!==0x50523654||v.getUint16(p+4,true)!==0x10f){editName(state);return;}
  interruptAll(v,11);v.setInt16(0x19fa+(selected%15)*288,14,true);v.setUint32(0x139c,(v.getUint32(0x139c,true)&0xffff6060)|0xff6060,true);v.setUint32(0x14bc,(v.getUint32(0x14bc,true)&0xff606060)|0x606060,true);v.setInt32(0x9e94,14,true);v.setInt32(0x9e7c,0,true);v.setInt32(0,0,true);return;
 }
 if(edge(512)){sound(11);v.setInt32(0x9e94,v.getUint8(0x9e9a)?2:10,true);interruptAll(v,2);v.setInt32(0x4450,0,true);}
}
// State14 overwrite prompt, 71464..7169f. Selection colors update before input.
export function advanceResultReplayOverwrite(state,services={}){
 const {v}=state,{held=0,previous=0,repeat=0,soundSlots=[-1,-1,-1],soundDisabled=false}=services,edge=bit=>(held&bit)!==0&&(held&bit)!==(previous&bit),sound=()=>queueSound(soundSlots,12,{disabled:soundDisabled});
 if(v.getInt32(0x9e94,true)!==14)throw Error('TH06nc result: replay overwrite state required');let selected=v.getInt32(0x9e7c,true),left=v.getUint32(0x139c,true),right=v.getUint32(0x14bc,true);
 if(selected===0){right=(right&0xff606060)|0x606060;left=(left&0xffff6060)|0xff6060;}else{right=(right&0xffff6060)|0xff6060;left=(left&0xff606060)|0x606060;}v.setUint32(0x139c,left,true);v.setUint32(0x14bc,right,true);if(v.getInt32(0x4450,true)<20)return;
 if((held&64)&&(edge(64)||repeat)){selected--;if(selected<0)selected+=2;sound();}else if((held&128)&&(edge(128)||repeat)){selected++;if(selected>=2)selected-=2;sound();}v.setInt32(0x9e7c,selected,true);
 if(edge(512)||edge(1024)){initializeResultReplayList(state,services);return;}
 if(edge(256)){v.setInt32(0x4450,0,true);if(selected===0)editName(state);else initializeResultReplayList(state,services);}
}
