import {queueSound} from './sound-queue.mjs';
// Result states 10/11, 72175..726c6. The replay-list loader 6d310 is
// an explicit service boundary; invoking it does not assert a saved replay.
export function advanceResultReplayGate({v},{held=0,previous=0,repeat=0,continuesUsed=0,soundSlots=[-1,-1,-1],soundDisabled=false,openReplayList=null}={}){
 const sound=id=>queueSound(soundSlots,id,{disabled:soundDisabled}),state=v.getInt32(0x9e94,true),clock=v.getInt32(0x4450,true),edge=bit=>(held&bit)!==0&&(held&bit)!==(previous&bit),interruptAll=()=>{for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,2,true);},close=()=>{v.setInt32(0x4450,0,true);sound(11);v.setInt32(0x9e94,2,true);interruptAll();};
 if(state===11){if(clock>=20&&(edge(256)||edge(512)))close();return;}
 if(state!==10)throw Error('TH06nc result: replay gate state required');
 if(clock===60){const request=(continuesUsed&255)?12:9;for(let i=1;i<=38;i++)v.setInt16(0xb0+i*288+0x8a,request,true);if(request!==9)v.setInt32(0x9e94,11,true);v.setInt32(0x9e7c,0,true);}
 const selected=v.getInt32(0x9e7c,true);let left=v.getUint32(0x139c,true),right=v.getUint32(0x14bc,true);
 if(selected===0){right=(right&0xff606060)|0x606060;left=(left&0xffff6060)|0xff6060;}else{right=(right&0xffff6060)|0xff6060;left=(left&0xff606060)|0x606060;}
 v.setUint32(0x139c,left,true);v.setUint32(0x14bc,right,true);if(clock<80)return;
 let selection=selected;if((held&64)&&(edge(64)||repeat)){selection=(selection-1)|0;if(selection<0)selection+=2;sound(12);}
 else if((held&128)&&(edge(128)||repeat)){selection=(selection+1)|0;if(selection>=2)selection-=2;sound(12);}
 v.setInt32(0x9e7c,selection,true);
 if(edge(512)||edge(1024)){close();return;}
 if(edge(256)){if(selection===0)openReplayList?.();else close();}
}
