import {applyMessageCommand} from './message-command.mjs';
const F=Math.fround;
// Whole 3eee0 message step. Scene-state requests are consumed by the host.
export function advanceMessage(state,{input=0,previousInput=0,...services}={}){
 const {v,environment}=state,sync=()=>{environment.messageField36b0=v.getInt32(0x36b0,true);environment.messageField3b50=v.getUint32(0x3b50,true);};
 if(v.getInt32(0x36b0,true)<0){sync();return -1;}
 if(v.getInt32(0x3b50,true)!==0)v.setInt32(0x3b50,(v.getInt32(0x3b50,true)-1)|0,true);
 let cursor=Number(v.getBigUint64(0x3668,true)),ins=state.instructions.get(cursor);if(!ins)throw Error('TH06nc message: invalid instruction pointer');
 if(v.getUint8(0x3900)&&(input&8)){v.setInt32(0x3908,ins.time,true);v.setInt32(0x3904,-999,true);}
 let yielded=false,budget=10000;
 while(v.getInt32(0x3908,true)>=ins.time){
  if(--budget<=0)throw Error('TH06nc message: non-yielding script');const action=applyMessageCommand(state,ins,{input,previousInput,...services});
  if(action==='end'){sync();return -1;}if(action==='return'){sync();return 0;}if(action==='wait'){yielded=true;break;}
  cursor+=ins.length;v.setBigUint64(0x3668,BigInt(cursor),true);ins=state.instructions.get(cursor);if(!ins)throw Error('TH06nc message: command advances outside script');
 }
 if(!yielded){const frame=v.getInt32(0x3908,true);v.setInt32(0x3904,frame,true);v.setInt32(0x3908,(frame+1)|0,true);}
 for(const offset of [0x3b60,0x3428,0x3548,0x36b8,0x37d8,0x3910,0x3a30])state.vm(offset).tick();
 let frame=v.getInt32(0x3908,true);if(frame<60&&v.getUint8(0x3900)&&(input&8)){frame=60;v.setInt32(0x3908,60,true);v.setInt32(0x3904,-999,true);}
 const alpha=Math.trunc(F(F(frame>=60?F(1):F(F(frame)/F(60)))*F(255)))&255;v.setUint32(0x3c4c,(v.getUint32(0x3c4c,true)&0xffffff)|(alpha<<24),true);sync();return 0;
}
