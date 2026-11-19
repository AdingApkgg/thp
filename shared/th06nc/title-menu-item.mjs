// Native menu-item presentation update, 0x14004d8e0..0x14004da70.
// Owner supplies its group, selected item and pulse clock; input/state changes
// remain separate from this sprite/alpha update.
export function updateTitleMenuItem(vm,{group,item,selected,activeGroup,pulse}){
 const v=vm.v,id=v.getInt16(0x36,true);
 if(item!==selected){vm.bindSprite(id);v.setFloat32(0xe8,1,true);v.setFloat32(0xe4,1,true);}
 else if(id>=0x100&&id<=0x132)vm.bindSprite(id+0xad);
 else if(id>=0x146&&id<=0x17c)vm.bindSprite(id+0x9a);
 for(const p of [0x18,0x1c,0x20])v.setFloat32(p,0,true);
 let alpha=255;
 if(group!==activeGroup)alpha=135;
 else if(item===selected){
  const t=pulse-Math.trunc(pulse/72)*72;
  if(t<30)alpha=128+Math.trunc(t*127/30);
  else if(t>=42)alpha=128+Math.trunc((72-t)*127/30);
 }
 v.setUint8(0xef,alpha);
}
