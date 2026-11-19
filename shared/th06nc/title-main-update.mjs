import {navigateTitle} from './title-navigation.mjs';
import {transitionTitleMain} from './title-main-transition.mjs';
// State-3 composition. Caller owns clocks, physical key sampling, unlock data,
// fade/audio delivery and destination menu owners.
export function updateTitleMain(group,initial,keys,{extraAvailable=false,disabled=new Uint8Array(173),fades=new Int32Array(10),sound={}}={}){
 if(initial.state!==3)throw Error('TH06nc: main-menu updater requires owner state 3');
 const state={...initial};
 const navigation=navigateTitle(state.selection,10,keys,sound);
 state.selection=navigation.selection;
 if(state.selection===1&&!extraAvailable)state.selection=navigation.direction+1;
 if(state.selection!==initial.selection)fades[initial.selection]=15;
 for(let item=0;item<10;item++){
  const index=item===3?50:item>3?item-1:item;
  if(disabled[index])continue;
  const vm=group.slots.get(0x9640+index*288);if(!vm)throw Error('TH06nc: missing main-menu VM');
  const v=vm.v,id=v.getInt16(0x36,true);
  vm.bindSprite(id+(item===state.selection?0xad:0));
  for(const p of [0x18,0x1c,0x20])v.setFloat32(p,0,true);
  let alpha=128;
  if(item===state.selection){
   const t=state.pulse-Math.trunc(state.pulse/72)*72;
   alpha=t<30?128+Math.trunc(t*127/30):t<42?255:128+Math.trunc((72-t)*127/30);
   fades[item]=0;
  }else if(fades[item]>0){alpha=128+Math.trunc((fades[item]*76-76)/14);fades[item]--;}
  v.setUint32(0xec,((alpha&255)<<24)|0xffffff,true);
 }
 const result=transitionTitleMain(state,keys,{extraAvailable});
 if(result.interrupt!==null)for(const [offset,vm]of group.slots)if(offset>=0x9640&&offset<0x15900)vm.interrupt(result.interrupt);
 return {...result,fades,soundSlots:navigation.soundSlots,direction:navigation.direction};
}
