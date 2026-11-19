import {AnmBank} from './anm-bank.mjs';
import {rebindAnm} from './anm-rebind.mjs';
export const titleReplayResources=Object.freeze([
 {file:'replay00.anm',slot:41,base:0x193},
 {file:'difficulty.anm',slot:66,base:0x792},
]);
// Title replay resource/VM entry 489f2..48ab7, excluding file loading. Position
// anchors are real replay00 ANMs; the text renderer reads their c8 coordinates.
export function initializeTitleReplayAnimations(group,resources,{disabled=new Uint8Array(173)}={}){
 for(const ref of titleReplayResources)group.bank.load(resources.get(ref.file),ref.base,{slot:ref.slot});
 const empty=new AnmBank(),difficulty=rebindAnm(empty,0,new Uint8Array(288),{resolveSprite:id=>group.bank.sprites.get(id)});difficulty.v.setUint16(0x108,0xf0f,true);difficulty.v.setInt32(0xb4,-1,true);difficulty.bindSprite(0x792);difficulty.v.setUint32(0xc4,(difficulty.v.getUint32(0xc4,true)&~0x300)|0x401,true);group.slots.set(0x16050,difficulty);
 for(let i=0;i<26;i++){
  const offset=0x13ba0+i*288,old=group.slots.get(offset);if(old)old.v.setUint32(0xc4,old.v.getUint32(0xc4,true)&~1,true);
  if(disabled[147+i])continue;
  const vm=group.bank.createVm(0x193+i,{allowMissing:true});vm.tick();vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|8|0x2000,true);vm.v.setUint32(0xec,0xffffffff,true);for(const p of [0x18,0x1c,0x20])vm.v.setFloat32(p,0,true);vm.v.setUint16(0x36,vm.v.getUint16(0x34,true),true);group.slots.set(offset,vm);
 }
}
