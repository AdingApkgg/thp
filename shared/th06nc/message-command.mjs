import {applyMessageMusic} from './message-music.mjs';
import {applyMessageProgress} from './message-progress.mjs';
import {createMusicState,fadeMessageMusic} from './music-state.mjs';
// Common dialog commands in 3eee0. Expensive text texture publication is a
// state-changing service, shared with the general HUD font implementation.
export function applyMessageCommand(state,ins,{input=0,previousInput=0,publishText=null,localization=null,...services}={}){
 const {v}=state,a=new DataView(ins.args.buffer,ins.args.byteOffset,ins.args.byteLength),short=p=>a.getInt16(p,true),op=ins.opcode;
 const text=(offset,key,speaker)=>{if(!publishText)throw Error('TH06nc message: text texture publisher missing');publishText({offset,key,text:localization?.[key]??key,colors:[0x3670,0x3680,0x3690,0x36a0].map(p=>v.getUint32(p+speaker*4,true))});};
 if(op===0){v.setInt32(0x36b0,-1,true);return 'end';}
 if(op===1){const speaker=short(0),variant=short(2);state.rebind(0x3428+speaker*288,(speaker===0?0x4c0:0x4c2)+variant);}
 else if(op===2){const speaker=short(0);state.vm(0x3428+speaker*288).bindSprite((speaker===0?0x4c0:0x4c6)+short(2));}
 else if(op===3||op===8){
  const speaker=short(0),line=short(2),offset=(op===3?0x36b8:0x3910)+line*288;
  if(op===3&&line===0&&v.getInt16(0x3810,true)>=0)text(0x37d8,' ',speaker);
  state.rebind(offset,(op===3?0x731:0x733)+line);
  if(op===3){const mode=v.getUint8(0x3424);v.setUint8(offset+0x109,mode);v.setUint8(offset+0x108,mode);}
  const tail=ins.args.subarray(4),end=tail.indexOf(0);if(end<0)throw Error('TH06nc message: unterminated localization key');const key=new TextDecoder('utf-8',{fatal:true}).decode(tail.subarray(0,end));text(offset,key,speaker);v.setInt32(0x3420,0,true);
 }else if(op===4){
  if(v.getUint8(0x3900)&&(input&8))return 'advance';const current=input&0x301;
  if(current&&current!==(previousInput&0x301)&&v.getInt32(0x3420,true)>=8)return 'advance';
  const clock=v.getInt32(0x3420,true);if(clock>=a.getInt32(0,true))return 'advance';v.setInt32(0x3420,(clock+1)|0,true);return 'wait';
 }else if(op===5){const slot=short(0);v.setUint16((slot<2?0x34b2:0x3502)+slot*288,a.getUint8(2),true);}
 else if(op===6)v.setInt32(0x3b50,(v.getInt32(0x3b50,true)+1)|0,true);
 else if(op===7)applyMessageMusic(state,a.getInt32(0,true),{publishText,localization,...services});
 else if(op===9||op===11||op===14)return applyMessageProgress(state,op,services);
 else if(op===10)return 'wait';
 else if(op===12)fadeMessageMusic(state.environment.musicState??=createMusicState());
 else if(op===13)v.setUint8(0x3900,a.getUint8(0));
 else if(op>=0&&op<=14)throw Error(`TH06nc message: command ${op} not implemented`);
 return 'advance';
}
