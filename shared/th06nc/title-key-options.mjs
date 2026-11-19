import {navigateTitle} from './title-navigation.mjs';
import {queueSound} from './sound-queue.mjs';
export const controllerKeyValues=[12,13,14,15,8,9,16,17,6,7,4,5];
export const defaultControllerKeys=[12,13,9,14,4];
export const controllerIconAssets=['button_xbox.anm','button_ps.anm','button_ns.anm'].map(file=>({archive:'th06TL.dat',file,slot:65,base:0x787}));

// Original state6 controller-button configuration49acc..4aa92. Button bytes
// are the native input owner's18-byte state, distinct from menu key bits.
export function updateTitleKeyOptions(group,initial,keys,{config,runtimeKeys,buttons=new Uint8Array(18),buttonState,deviceKind=0,iconState,loadButtonIcons,sound={}}={}){
 if(initial.state!==6)throw Error('TH06nc: key options owner required');
 const state={...initial,keySelections:[...initial.keySelections]},effects=[];
 if(deviceKind!==iconState.kind){iconState.kind=deviceKind;loadButtonIcons(controllerIconAssets[deviceKind===1?1:deviceKind===2?2:0]);effects.push({kind:'loadButtonIcons',deviceKind});}
 const navigation=navigateTitle(state.selection,8,keys,sound),sounds=navigation.soundSlots;state.selection=navigation.selection;
 const t=state.pulse-Math.trunc(state.pulse/72)*72,alpha=t<30?128+Math.trunc(Math.imul(t,127)/30):t<42?255:128+Math.trunc(Math.imul(72-t,127)/30),pulse=(alpha<<24)>>>0,base=state.menuColor??0;
 const paint=(offset,selected,{highlight=true}={})=>{const vm=group.slots.get(offset),v=vm.v;vm.bindSprite(v.getInt16(0x36,true)+(selected&&highlight?0x9a:0));for(const p of[0x18,0x1c,0x20])v.setUint32(p,0,true);v.setUint32(0xec,((selected?pulse:base)|0xffffff)>>>0,true);};
 for(const [offset,row]of [[0x10c60,0],[0x10b40,0],[0xe500,1],[0xe620,2],[0xe740,3],[0xe860,4],[0x10ea0,5],[0xe980,6],[0xeaa0,7]])paint(offset,row===state.selection&&(offset!==0x10b40||state.frame>=32));
 const symbol=(offset,index,color)=>{const vm=group.slots.get(offset),v=vm.v;v.setUint32(0xc4,index<0?v.getUint32(0xc4,true)&~2:v.getUint32(0xc4,true)|2,true);if(index<0)return;vm.bindSprite(0x787+index);v.setUint16(0x36,v.getUint16(0x34,true),true);vm.bindSprite(v.getInt16(0x36,true));v.setUint32(0xec,color>>>0,true);for(const p of[0x18,0x1c,0x20])v.setUint32(p,0,true);};
 state.keySelections.forEach((index,i)=>symbol(0xebc0+i*288,index,((state.selection===i+1?pulse:base)|0xffffff)>>>0));
 const fixed=[controllerKeyValues.indexOf(12+Number(config[22]!==0)),controllerKeyValues.indexOf(config[22]?12:13)];
 fixed.forEach((index,i)=>{const vm=group.slots.get(0xf160+i*288),v=vm.v;vm.bindSprite(0x787+index);v.setUint16(0x36,v.getUint16(0x34,true),true);paint(0xf160+i*288,state.selection===0,{highlight:false});});
 for(const [offset,index]of [[0xf3a0,fixed[0]],[0xf4c0,fixed.includes(state.keySelections[0])?-1:state.keySelections[0]],[0xf5e0,fixed[1]],[0xf700,fixed.includes(state.keySelections[1])?-1:state.keySelections[1]]])symbol(offset,index,0xffffffff);
 if(state.frame<32)return {state,effects,soundSlots:sounds};
 const edge=bit=>Boolean(keys.held&bit)&&((keys.previous&bit)!==(keys.held&bit)),pressed=bit=>Boolean(keys.held&bit)&&(edge(bit)||keys.repeat!==0),play=id=>queueSound(sounds,id,{disabled:sound.disabled});
 let button=controllerKeyValues.findIndex(code=>buttons[code]);if(button<0)button=12;
 if(button<12&&button!==buttonState.previous&&state.selection>=1&&state.selection<=5){
  play(10);const selected=state.selection-1,old=state.keySelections[selected],special=selected===0||selected===2;
  state.keySelections=state.keySelections.map((index,i)=>(!special||(i!==0&&i!==2))&&index===button?old:index);state.keySelections[selected]=button;
 }
 buttonState.previous=button;
 if(state.selection===0&&(pressed(64)||pressed(128))){play(12);config[22]=Number(config[22]===0);for(const offset of[0xf160,0xf280])group.slots.get(offset).interrupt(pressed(64)?26:27);}
 if(edge(256)){
  if(state.selection===6){play(10);state.keySelections=defaultControllerKeys.map(code=>controllerKeyValues.indexOf(code));config[22]=0;}
  else if(state.selection===7){
   state.state=4;state.frame=0;state.pulse=0;state.selection=6;
   for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900){const index=(p-0x9640)/288;vm.interrupt(index>=51&&index<=69?0:3);}play(11);
   const v=new DataView(runtimeKeys.buffer,runtimeKeys.byteOffset,10),cv=new DataView(config.buffer,config.byteOffset,44);state.keySelections.forEach((index,i)=>{const value=index===-1?0:controllerKeyValues[index];v.setUint16(i*2,value,true);cv.setUint16(i*2,value,true);});
  }
 }
 return {state,effects,soundSlots:sounds};
}
