import {navigateTitle} from './title-navigation.mjs';
import {updateTitleMenuItem} from './title-menu-item.mjs';
import {queueSound} from './sound-queue.mjs';
import {defaultEnvironmentConfig} from './config-file.mjs';
const order=[1,0,2],activeSize=b=>b[b[4]===1?6:b[4]===2?7:5];

// Original display submenu helper4dc90..4e87c, including immediate render
// reconfiguration requests. Platform operations are delivered by the owner.
export function updateTitleDisplayOptions(group,initial,keys,{environmentConfig:env,sound={}}={}){
 if(initial.state!==7)throw Error('TH06nc: display options owner required');
 const state={...initial},effects=[],navigation=navigateTitle(state.selection,5,keys,sound),sounds=navigation.soundSlots;state.selection=navigation.selection;
 if(navigation.direction&&state.selection===1&&env[4]===1)state.selection=navigation.direction===1?2:0;
 const t=state.pulse-Math.trunc(state.pulse/72)*72,alpha=t<30?128+Math.trunc(Math.imul(t,127)/30):t<42?255:128+Math.trunc(Math.imul(72-t,127)/30);
 for(let row=0;row<5;row++){
  const vm=group.slots.get(0x11200+row*288),v=vm.v;v.setUint32(0xc4,v.getUint32(0xc4,true)|2,true);vm.bindSprite(v.getInt16(0x36,true)+(row===state.selection?0x9a:0));for(const p of[0x18,0x1c,0x20])v.setUint32(p,0,true);v.setUint32(0xec,((row===state.selection?alpha<<24:state.menuColor??0)|0xffffff)>>>0,true);
 }
 const present=(offset,activeGroup,item,selected)=>updateTitleMenuItem(group.slots.get(offset),{group:activeGroup,item,selected,activeGroup:state.selection,pulse:state.pulse});
 for(let item=0;item<3;item++)present(0x117a0+item*288,0,item,env[4]);
 const size=activeSize(env);
 for(let item=0;item<5;item++){const offset=0x11b00+item*288,v=group.slots.get(offset).v,visible=env[4]!==1&&size===item;v.setUint32(0xc4,visible?v.getUint32(0xc4,true)|2:v.getUint32(0xc4,true)&~2,true);if(visible)present(offset,1,item,item);}
 for(let item=0;item<2;item++)present(0x120a0+item*288,2,item,Number(env[8]===0));
 if(state.frame<32)return {state,effects,soundSlots:sounds};
 const edge=bit=>Boolean(keys.held&bit)&&((keys.previous&bit)!==(keys.held&bit)),pressed=bit=>Boolean(keys.held&bit)&&(edge(bit)||keys.repeat!==0),play=id=>queueSound(sounds,id,{disabled:sound.disabled});
 const change=direction=>{
  if(state.selection<0||state.selection>2)return;play(12);
  if(state.selection===0){let index=order.indexOf(env[4]);if(index<0)index=0;env[4]=order[(index+(direction<0?2:1))%3];}
  else if(state.selection===1){const offset=env[4]===1?6:env[4]===2?7:5;do{env[offset]=(env[offset]+(direction<0?4:1))%5;}while(env[offset]===0&&env[4]===0);}
  else env[8]=Number(env[8]===0);
 };
 if(pressed(64))change(-1);if(pressed(128))change(1);
 if(state.selection===1&&env[4]===1)state.selection=2;
 if(edge(512)){state.selection=4;play(11);}
 if(edge(256)){
  if(state.selection===3){play(10);env.set(defaultEnvironmentConfig());state.selection=0;}
  else if(state.selection===4){
   play(11);const old=state.environmentConfig;
   if(old[4]!==env[4]||old[8]!==env[8]||activeSize(old)!==activeSize(env)){effects.push({kind:'setDisplayFlag',enabled:env[8]!==0});if(env[4]<=2)effects.push({kind:'applyDisplayMode',mode:env[4]});effects.push({kind:'saveEnvironmentConfig'});}
   state.state=4;state.frame=0;state.pulse=0;state.selection=5;
   for(const [p,vm]of group.slots)if(p>=0x9640&&p<0x15900){const index=(p-0x9640)/288;vm.interrupt(index>=51&&index<=69?0:3);}
  }
 }
 return {state,effects,soundSlots:sounds};
}
