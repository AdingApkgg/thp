import {navigateTitle} from './title-navigation.mjs';
import {updateTitleMenuItem} from './title-menu-item.mjs';
import {queueSound} from './sound-queue.mjs';
import {resetGameConfig} from './config-file.mjs';
const rootItems=[9,10,11,12,13,49,109,108,15],keyValues=[12,13,14,15,8,9,16,17,6,7,4,5];

// Native title Options state4, 490d2..49acc. Configuration, sound/music and
// file writes belong to the supervisor; returned effects preserve call order.
export function updateTitleOptions(group,initial,keys,{config,runtimeKeys,environmentConfig,disabled=new Uint8Array(173),sound={}}={}){
 if(initial.state!==4)throw Error('TH06nc: options owner required');
 const state={...initial},effects=[],navigation=navigateTitle(state.selection,9,keys,sound);state.selection=navigation.selection;const sounds=navigation.soundSlots,play=id=>queueSound(sounds,id,{disabled:sound.disabled}),edge=bit=>Boolean(keys.held&bit)&&((keys.previous&bit)!==(keys.held&bit)),pressed=bit=>Boolean(keys.held&bit)&&(edge(bit)||keys.repeat!==0);
 const present=(index,activeGroup,item,selected)=>{if(disabled[index])return;const vm=group.slots.get(0x9640+index*288);if(vm)updateTitleMenuItem(vm,{group:activeGroup,item,selected,activeGroup:state.selection,pulse:state.pulse});};
 rootItems.forEach((index,item)=>present(index,item,item,state.selection));
 for(const [start,count,activeGroup,selected]of [[16,5,0,config[16]],[21,4,1,config[17]],[25,10,2,config[18]],[35,10,3,config[19]],[45,2,4,config[20]]])for(let item=0;item<count;item++)present(start+item,activeGroup,item,selected);
 if(state.frame<32)return {state,effects,soundSlots:sounds};
 const change=direction=>{
  const item=state.selection;if(item<0||item>4)return;
  const offset=16+item,old=config[offset];
  if(item===2||item===3){if((direction<0&&old>0)||(direction>0&&old<9)){play(12);config[offset]=(old+direction)&255;}if(item===2)effects.push({kind:'applyMusicVolume'});}
  else{play(12);const count=[5,4,0,0,2][item];config[offset]=direction<0?(old===0?count:old)-1:old+1>=count?0:old+1;if(item===4)effects.push({kind:'restartTitleMusic'});}
 };
 if(pressed(64))change(-1);
 if(edge(512)){state.selection=8;play(11);}
 if(pressed(128))change(1);
 if(edge(256)){
  if(state.selection===5){state.state=7;state.frame=0;state.pulse=0;state.environmentConfig=environmentConfig.slice();state.selection=0;for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(25);play(10);}
  else if(state.selection===6){state.state=6;state.frame=0;state.pulse=0;state.selection=0;for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900)vm.interrupt(5);play(10);const kv=new DataView(runtimeKeys.buffer,runtimeKeys.byteOffset,10);state.keySelections=Array.from({length:5},(_,i)=>keyValues.indexOf(kv.getInt16(i*2,true)));}
  else if(state.selection===7){effects.push({kind:'resetSound'});resetGameConfig(config,runtimeKeys);effects.push({kind:'restartTitleMusic'});}
  else if(state.selection===8){
   state.state=3;state.frame=0;state.pulse=0;state.menuFadeTicks=0;state.menuFadeDuration=0;state.menuFadePreviousDuration=0;state.menuFadeStartColor=0;state.menuFadeEndColor=0;state.menuFadeClock=0;
   for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900){const index=(p-0x9640)/288;vm.interrupt(index>=51&&index<=69?0:2);}
   for(const index of [0,1,2,50,3,4,5,6,7,8])group.slots.get(0x9640+index*288)?.interrupt(28);
   state.inputDelay=10;state.entryHold=true;state.selection=8;play(11);effects.push({kind:'saveConfig'},{kind:'saveEnvironmentConfig'});
  }
 }
 return {state,effects,soundSlots:sounds};
}

