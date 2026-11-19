import {spellPulseAlpha} from './spell-practice-draw-effects.mjs';
const F=Math.fround,metric=x=>F(F(F(x)*F(480))/F(1080));
const copy=vm=>{const result=Object.assign(Object.create(Object.getPrototypeOf(vm)),vm);result.state=vm.state.slice();result.v=new DataView(result.state.buffer);return result;};
const available=(vm,hasTexture)=>vm?.pointer(0x100)&&vm.boundBinding?.active!==false&&hasTexture(vm);
const progress=ticks=>{const elapsed=(10-(ticks|0))|0;if(elapsed<=0)return F(0);if(elapsed>=10)return F(1);const t=F(F(1)-F(F(elapsed)/F(10)));return F(F(1)-F(F(t*t)*t));};
const alphaColor=a=>((a<<24)|0xffffff)>>>0;

// 4f3c0: retained shot-preview VM, placed against the right framebuffer edge.
export function drawSpellProfilePreview(group,state,draw,{width=1920,height=1080,hasTexture=()=>true}={}){
 const vm=group.slots.get(0x1a5f8);if(!vm||!(vm.v.getUint32(0xc4,true)&1)||!available(vm,hasTexture)||height<=0)return;
 const v=vm.v,sprite=vm.boundSprite;v.setUint32(0xc4,(v.getUint32(0xc4,true)&~0x200)|0x500,true);
 v.setFloat32(0xc8,F(F(F(width)*F(480))/F(height)),true);v.setFloat32(0xcc,F(F(480)-F(metric(sprite.height)*v.getFloat32(0xe4,true))),true);
 const opacity=progress(state.orderTransition),pulse=spellPulseAlpha(state.pulse??0,128),alpha=(179+Math.trunc((pulse-128)*76/127))&255;
 v.setUint32(0xec,alphaColor(opacity<=0?0:opacity>=1?alpha:Math.trunc(F(F(F(alpha)*opacity)+F(.5)))),true);draw(vm,{snap:true});
}

// 4f5b0 with nested label helper 4fc00: character crossfade, shot label and
// mirrored decorative strips. Temporary label VMs never replace their owners.
export function drawSpellProfileLabels(group,state,draw,{character,shot,hasTexture=()=>true}={}){
 let entryAlpha=255,entryShift=F(0),shotEntry=F(1);
 if(state.fastEntry&&state.state===28){
  const frame=state.frame|0;
  if(frame<=10){entryAlpha=0;entryShift=F(56);shotEntry=F(0);}
  else{
   if(frame<42){const t=F(F(1)-F(F(frame-10)*F(.03125))),p=F(F(1)-F(F(t*t)*t));entryAlpha=Math.trunc(F(F(p*F(255))+F(.5)));entryShift=F(F(F(1)-p)*F(56));}
   if(frame<=16)shotEntry=F(0);else if((frame>>>0)<44){const t=F(F(1)-F(F(frame-16)/F(28)));shotEntry=F(F(1)-F(F(t*t)*t));}
  }
 }
 const label=(c,x,alpha)=>{
  const original=group.slots.get(0x12400+c*576),a=Math.trunc(Math.imul(alpha,entryAlpha)/255);if(!available(original,hasTexture)||a<=0)return;
  const vm=copy(original),v=vm.v;v.setUint32(0xc4,v.getUint32(0xc4,true)|3,true);v.setFloat32(0xc8,F(F(x)+entryShift),true);v.setFloat32(0xcc,F(282.6666564941406),true);v.setFloat32(0xe8,F(.8),true);v.setFloat32(0xe4,F(.8),true);v.setUint32(0xec,alphaColor(a),true);draw(vm,{snap:true});
 };
 let smooth=F(1),remaining=F(0);
 if((state.stageTransition|0)>0){const t=F(F((10-(state.stageTransition|0))|0)/F(10));smooth=F(F(F(3)-F(t+t))*F(t*t));remaining=F(F(1)-smooth);label(1-(character&255),F(F(625)-F(F(smooth*F(state.stageDirection|0))*F(8))),Math.trunc(F(remaining*F(255))));}
 label(character&255,F(F(F(remaining*F(state.stageDirection|0))*F(16))+F(625)),Math.trunc(F(smooth*F(255))));
 const original=group.slots.get(0x13060+((character&255)*2+(shot&255))*288);
 if(available(original,hasTexture)){
  const vm=copy(original),v=vm.v,p=progress(state.orderTransition);
  v.setUint32(0xc4,v.getUint32(0xc4,true)|3,true);v.setFloat32(0xe8,F(v.getFloat32(0xe8,true)*F(.6899999976158142)),true);v.setFloat32(0xe4,F(v.getFloat32(0xe4,true)*F(.6899999976158142)),true);
  let x=F(F(F(1)-shotEntry)*F(28));x=F(x+F(598.888916015625));let shift=F(F(state.orderDirection|0)*F(F(1)-p));shift=F(shift*F(16));x=F(shift+x);
  v.setFloat32(0xc8,x,true);v.setFloat32(0xcc,F(405.6666564941406),true);
  const a=Math.trunc(F(F(p*F(191))+F(64))),b=Math.trunc(Math.imul(a,original.v.getUint8(0xef))/255),c=Math.trunc(F(F(shotEntry*F(255))+F(.5)));
  v.setUint32(0xec,alphaColor(Math.trunc(Math.imul(b,c)/255)),true);draw(vm,{snap:true});
 }
 const border=group.slots.get(0x1a4d8);if(!available(border,hasTexture))return;
 const v=border.v,ticks=state.orderTransition|0,direction=ticks>0?state.orderDirection|0:0,q=ticks>0?F(F(F(ticks)/F(10))*F(F(ticks)/F(10))):F(0),span=F(F(metric(border.boundSprite.width)*F(.10000000149011612))+F(4));
 v.setUint32(0xec,alphaColor(Math.trunc(Math.imul(spellPulseAlpha(state.pulse??0,128),entryAlpha)/255)),true);v.setUint32(0xc4,v.getUint32(0xc4,true)|1,true);v.setFloat32(0xcc,F(234.6666717529297),true);
 const left=direction===-1?q:F(0);v.setFloat32(0xc8,F(F(614)-F(span*left)),true);v.setFloat32(0xe8,F(F(left*F(.10000000149011612))+F(1)),true);draw(border,{snap:true});
 const right=direction===1?q:F(0);v.setFloat32(0xc8,F(F(span*right)+F(835)),true);v.setFloat32(0xe8,F(F(F(right*F(.10000000149011612))+F(1))*F(-1)),true);draw(border,{snap:true});
}
