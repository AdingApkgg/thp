import {queueSound} from './sound-queue.mjs';
// Original 96-cell table at 30c250; final cells 94/95 mean Space/End.
export const scoreNameCharacters='ABCDEFGHIJKLMNOPQRSTUVWXYZ.,:;\\@abcdefghijklmnopqrstuvwxyz+-/*=%0123456789(){}[]<>#!?\'"$      --';
// 6d190 initializes the append cursor after trimming trailing spaces.
export function initializeScoreNameCursor({bytes,v}){
 let length=0;while(length<8&&bytes[0x9e70+length])length++;while(length>0&&bytes[0x9e70+length-1]===32)length--;v.setInt32(0x9e7c,length,true);v.setInt32(0,length>0?95:0,true);
}
// State-9 input portion 70dca..71435. The result owner owns its ANM tick,
// common frame increment, record qualification and transition destination.
export function advanceScoreNameInput({bytes,v},{held=0,previous=0,repeat=0,soundSlots=[-1,-1,-1],soundDisabled=false,achievement=null,saveName=null}={}){
 if(v.getInt32(0x4450,true)<30)return null;
 const edge=bit=>(held&bit)!==0&&(previous&bit)!==(held&bit),pressed=bit=>(held&bit)!==0&&(edge(bit)||repeat!==0),sound=id=>queueSound(soundSlots,id,{disabled:soundDisabled}),get=()=>v.getInt32(0,true),set=x=>v.setInt32(0,x,true),space=()=>scoreNameCharacters.charCodeAt(get())===32;
 if(pressed(16)){do{let x=get()-16;if(x<0)x+=96;set(x);}while(space());sound(12);}
 if(pressed(32)){do{let x=get()+16;if(x>=96)x-=96;set(x);}while(space());sound(12);}
 if(pressed(64)){do{let x=get()-1;if(x%16===15)x+=16;if(x<0)x=15;set(x);}while(space());sound(12);}
 if(pressed(128)){do{let x=get()+1;if(x%16===0)x-=16;set(x);}while(space());sound(12);}
 const finish=()=>{
  sound(11);achievement?.('Achievement21');saveName?.(bytes.slice(0x9e70,0x9e79));v.setInt32(0x9e94,15,true);v.setInt32(0x4450,0,true);for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,2,true);
  for(let i=0;i<9;i++){bytes[0x9e88+i]=bytes[0x9e70+i];if(!bytes[0x9e70+i])break;}return {kind:'finishName'};
 };
 if(pressed(256)){
  const selection=get();if(selection>94)return finish();const length=v.getInt32(0x9e7c,true),index=length>=8?7:length;bytes[0x9e70+index]=selection===94?32:scoreNameCharacters.charCodeAt(selection);if(length<8){v.setInt32(0x9e7c,length+1,true);if(length+1===8)set(95);}sound(10);
 }
 if(pressed(512)){const length=v.getInt32(0x9e7c,true);if(length>0){v.setInt32(0x9e7c,length-1,true);bytes[0x9e70+length-1]=32;}sound(11);}
 if(edge(1024))return finish();return null;
}
