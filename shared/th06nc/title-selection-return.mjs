// Selection cancel state 10, 4b0d7..4b0f0. Common processing follows.
export function advanceSelectionReturn(initial){
 return initial.frame===30?{...initial,state:0,frame:0}:{...initial};
}
// Main-menu helper 4d370..4d67b, including the cold startup overlay branch.
// Resource unloading/rebinding precedes this helper in the application owner.
export function warmTitleMain(group,initial,backdrop,{disabled=new Uint8Array(173),hasTexture=()=>true}={}){
 initial={...initial,returnTweenTicks:0,returnTweenY:0,returnTweenX:0};
 for(let i=0;i<173;i++){
  const vm=group.slots.get(0x9640+i*288);if(!vm)continue;
  const v=vm.v;v.setUint32(0xc4,v.getUint32(0xc4,true)|8,true);vm.interrupt(1);v.setUint32(0xec,0xffffffff,true);
  for(const p of [0x18,0x1c,0x20])v.setUint32(p,0,true);
 }
 group.slots.get(0x16170).interrupt(1);group.slots.get(0x16290).interrupt(1);backdrop.counter=0;
 if(initial.startupOverlay){
  backdrop.counter=170;
  return {...initial,state:2,frame:0,inputCooldown:60,warmReturn:false,mainFastEntry:false};
 }
 for(let tick=0;tick<359;tick++){
  if(tick===169)backdrop.request(1);
  for(let i=51;i<70;i++){const vm=group.slots.get(0x9640+i*288);if(!disabled[i]&&vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm.boundResource??vm.resource))vm.tick();}
  backdrop.tick();
 }
 return {...initial,state:2,frame:0,pulse:0,inputCooldown:0,warmReturn:false,mainFastEntry:true,startupOverlay:false,menuFadeDuration:0};
}
// State-2 entry prefix 4801b..48174. Caller checks the cold input gate first.
export function finishWarmTitleMain(group,initial,{backdrop=null,fade=null}={}){
 const fast=Boolean(initial.mainFastEntry);
 let next={...initial};
 if(!fast){
  const color=group.slots.get(0x164d0).v;
  color.setUint32(0xec,color.getUint32(0xec,true)|0xff000000,true);
  if(backdrop?.counter>0){
   group.slots.get(0x163b0).v.setUint8(0xef,0);
   group.slots.get(0x165f0).v.setUint8(0xef,0);
   const control=group.slots.get(0x16710).v;
   control.setUint32(0xec,control.getUint32(0xec,true)|0xff000000,true);
  }
  if(initial.startupOverlay&&fade?.mode){
   const alpha=fade.alpha;
   fade.request(fade.color,8,3);
   fade.v.setInt32(0x2c,alpha,true);
  }
  const target=group.slots.get(0x9640+59*288).v;
  next={...next,returnTweenTicks:24,returnTweenY:target.getFloat32(0xe8,true),returnTweenX:target.getFloat32(0xe4,true)};
 }
 for(let i=0;i<173;i++)group.slots.get(0x9640+i*288)?.interrupt(fast&&i>=51&&i<=69?6:2);
 if(initial.startupOverlay||fast)for(const i of [0,1,2,50,3,4,5,6,7,8])group.slots.get(0x9640+i*288).interrupt(28);
 const index=initial.selection===3?50:initial.selection>3?initial.selection-1:initial.selection,v=group.slots.get(0x9640+index*288).v;
 v.setUint32(0xec,0xffffe0e0,true);for(const p of [0x18,0x1c,0x20])v.setUint32(p,0,true);
 return {...next,state:3,frame:0,pulse:0,warmReturn:fast,mainFastEntry:false,startupOverlay:false,entryHold:Boolean(initial.startupOverlay||fast),menuFadeDuration:60};
}

// State2 gate47f6a..47fa2. Compare the entire masked field, including releases
// of one key while another remains held. Warm reentry bypasses the gate.
export function titlePromptReady(state,{held=0,previous=0}={}){
 if(state.mainFastEntry)return true;
 if(state.frame<30)return false;
 const current=held&0x1f00;
 return current!==0&&current!==(previous&0x1f00);
}

// Native46e50, after title VM updates and before logo/background advancement.
export function advanceTitleReturnTween(group,state){
 if(!(state.returnTweenTicks>0))return state;
 const next={...state};
 if(state.state!==3){next.returnTweenTicks=0;return next;}
 const F=Math.fround;
 next.returnTweenTicks=(state.returnTweenTicks-1)|0;
 const ratio=F(F(next.returnTweenTicks)/F(24));
 const intermediate=F(1-ratio),remaining=F(1-intermediate);
 const eased=F(1-F(remaining*remaining));
 const target=group.slots.get(0x9640+59*288).v;
 for(const [offset,start]of [[0xe8,state.returnTweenY],[0xe4,state.returnTweenX]]){
  target.setFloat32(offset,F(F(F(1-start)*eased)+start),true);
 }
 return next;
}
