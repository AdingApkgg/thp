import {queueSound} from './sound-queue.mjs';
export function interruptScoreAnimations({v},request){for(let i=0;i<38;i++)v.setInt16(0xb0+i*288+0x8a,request,true);}
function rootColors({v}){
 const pulse=v.getInt32(0x4454,true),t=pulse-Math.trunc(pulse/72)*72,alpha=t<30?128+Math.trunc(Math.imul(t,127)/30):t<42?255:128+Math.trunc(Math.imul(72-t,127)/30),selected=v.getInt32(0x9e7c,true);
 for(let i=0;i<7;i++){const p=0xb0+(i+1)*288;v.setUint32(p+0xec,i===selected?((alpha<<24)|0xffffff)>>>0:0x60ffffff,true);for(const axis of [0x18,0x1c,0x20])v.setFloat32(p+axis,0,true);}
}
// Score-owner root states0/1, 6e4e0..6f9c0. Common result ANM/time tail is
// separate. X selects Return; confirming that item starts the black exit.
export function advanceScoreMenu(state,{held=0,previous=0,repeat=0,fade=null,spellRecords,soundSlots=[-1,-1,-1],soundDisabled=false}={}){
 const {v,bytes}=state,kind=v.getInt32(0x9e94,true),clock=v.getInt32(0x4450,true),get=()=>v.getInt32(0x9e7c,true),set=x=>v.setInt32(0x9e7c,x|0,true),edge=bit=>Boolean(held&bit)&&((held&bit)!==(previous&bit)),move=bit=>Boolean(held&bit)&&(edge(bit)||repeat!==0),sound=id=>queueSound(soundSlots,id,{disabled:soundDisabled});
 if(kind===0){
  if(clock===0){if(fade?.mode===2)fade.requestIn(0,30);interruptScoreAnimations(state,1);for(let i=0;i<38;i++){const p=0xb0+i*288+0xc4;v.setUint32(p,v.getUint32(p,true)|8,true);}}
  rootColors(state);if(clock<20)return;v.setInt32(0x9e94,1,true);v.setInt32(0x4450,0,true);
 }
 if(v.getInt32(0x9e94,true)!==1)throw Error('TH06nc score: root menu state required');
 if(move(16)){let selection=(get()-1)|0;if(selection<0)selection+=7;set(selection);sound(12);}
 if(move(32)){let selection=(get()+1)|0;if(selection>=7)selection-=7;set(selection);sound(12);}
 rootColors(state);
 if(edge(256)){
  const selected=get();
  if(selected>=0&&selected<=4){sound(10);interruptScoreAnimations(state,selected+3);v.setInt32(0xa8,selected,true);v.setInt32(0x9e94,selected+3,true);v.setInt32(0x9e9c,selected+3,true);set(v.getInt32(0x9e80,true));v.setInt32(0x4450,0,true);v.setInt32(4,-1,true);v.setInt32(0x18,-1,true);}
  else if(selected===5){
   sound(10);interruptScoreAnimations(state,8);v.setInt32(0xa8,5,true);v.setInt32(0x9e94,8,true);v.setInt32(0x9e9c,8,true);v.setInt32(0x4450,0,true);v.setInt32(4,-1,true);let count=0;
   for(let id=0;id<134;id++)if(id<131||spellRecords?.get(id)?.attempts)bytes[0x1c+count++]=id;
   v.setInt32(0xa4,count,true);const pages=Math.max(1,Math.trunc((count+9)/10)),page=v.getInt32(0x9e84,true);set(page>=pages?pages-1:page);v.setInt32(0x18,-1,true);
  }else if(selected===6){
   interruptScoreAnimations(state,2);for(const p of [0x403a,0x427a,0x415a])v.setInt16(p,2,true);v.setInt32(0x9e94,2,true);v.setInt32(0x4450,0,true);v.setUint8(0x9e98,1);fade?.requestOut(0,30);sound(11);
  }
 }
 if(edge(512)){set(6);sound(11);}
}
