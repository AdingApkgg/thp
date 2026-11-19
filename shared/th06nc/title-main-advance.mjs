// Stable state-3 common postprocessing, without return-to-main tween/slide.
// The state-changing common path is intentionally a separate owner task.
export function advanceStableTitleMain(group,state,backdrop,{disabled=new Uint8Array(173),hasTexture=()=>true,backgroundEnabled=true}={}){
 if(state.state!==3||state.returnTweenTicks>0||state.menuSlideTicks>0)throw Error('TH06nc: unsupported stable-main postprocessing state');
 const next={...state};
 if(!(next.entryHold&&next.frame<36)){const t=(next.pulse+1)|0;next.pulse=t-Math.trunc(t/72)*72;}
 next.frame=(next.frame+1)|0;next.totalFrame=((next.totalFrame??0)+1)|0;
 if(next.inputCooldown>0)next.inputCooldown--;
 if(backdrop.counter>0){backdrop.counter--;if(backdrop.counter===0)backdrop.request(1);}
 if(next.entryHold&&next.frame>=36)next.entryHold=false;
 if([4,6,7].includes(next.previousGroupState))group.slots.get(0x15990)?.interrupt(2);
 next.previousGroupState=3;
 for(let i=0;i<173;i++){
  const vm=group.slots.get(0x9640+i*288);
  if(!disabled[i]&&vm?.pointer(0x100)&&hasTexture(vm.boundResource??vm.resource))vm.tick();
 }
 const logo=group.slots.get(0x15990);
 if(logo?.pointer(0x100)&&hasTexture(logo.boundResource??logo.resource))logo.tick();
 if(backgroundEnabled&&hasTexture(group.slots.get(0x16290)?.boundResource))backdrop.tick();
 return next;
}
