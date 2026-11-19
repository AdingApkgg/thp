import {queueSound} from './sound-queue.mjs';
import {scoreNameCharacters} from './score-name-input.mjs';
import {initializeResultReplayList} from './result-replay-list-init.mjs';
// State13 input 7169f..71b7c. End writes/configures before the shared
// length/sound tail; Escape returns to the list, including after End in a chord.
export function advanceReplayNameInput(state,{held=0,previous=0,repeat=0,soundSlots=[-1,-1,-1],soundDisabled=false,recordingAvailable=false,writeReplay=null,saveName=null,readHeader=null,ensureDirectory=null}={}){
 const {bytes,v}=state;if(v.getInt32(0x4450,true)<30)return null;
 const edge=bit=>(held&bit)!==0&&(previous&bit)!==(held&bit),pressed=bit=>(held&bit)!==0&&(edge(bit)||repeat!==0),sound=id=>queueSound(soundSlots,id,{disabled:soundDisabled}),get=()=>v.getInt32(0,true),set=x=>v.setInt32(0,x,true),space=()=>scoreNameCharacters.charCodeAt(get())===32;
 if(pressed(16)){do{let x=get()-16;if(x<0)x+=96;set(x);}while(space());sound(12);}
 if(pressed(32)){do{let x=get()+16;if(x>=96)x-=96;set(x);}while(space());sound(12);}
 if(pressed(64)){do{let x=get()-1;if(x%16===15)x+=16;if(x<0)x=15;set(x);}while(space());sound(12);}
 if(pressed(128)){do{let x=get()+1;if(x%16===0)x-=16;set(x);}while(space());sound(12);}
 let finished=false;
 const finish=()=>{
  if(recordingAvailable)writeReplay?.({path:`replay/th6_${String(v.getInt32(0x4438,true)+1).padStart(2,'0')}.rpy`,name:bytes.slice(0x9e88,0x9e91),standalone:Boolean(bytes[0x9e9a])});saveName?.(bytes.slice(0x9e88,0x9e91));v.setInt32(0x9e94,2,true);v.setInt32(0x4450,0,true);for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,2,true);finished=true;
 };
 if(pressed(256)){
  const selection=get(),length=v.getInt32(0x9e7c,true),index=length>=8?7:length;if(selection>94)finish();else bytes[0x9e88+index]=selection===94?32:scoreNameCharacters.charCodeAt(selection);if(length<8){v.setInt32(0x9e7c,length+1,true);if(length+1===8)set(95);}sound(10);
 }
 if(pressed(512)){const length=v.getInt32(0x9e7c,true);if(length>0){v.setInt32(0x9e7c,length-1,true);bytes[0x9e88+length-1]=32;}sound(11);}
 if(edge(1024)){initializeResultReplayList(state,{soundSlots,soundDisabled,readHeader,ensureDirectory});return null;}return finished?{kind:'finishReplayName'}:null;
}
