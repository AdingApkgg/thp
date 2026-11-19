import {initializeSelectionAnimations} from './title-selection-layout.mjs';
import {AnmVm} from './anm-vm.mjs';

export const spellMenuAsset=Object.freeze({archive:'th06TL.dat',file:'spellselect00.anm',slot:67,base:0x7be});
export const spellMenuVmSlots=Object.freeze([
 [0x19998,0x7be],[0x19ab8,0x7bf],[0x19bd8,0x7c0],[0x19cf8,0x7c1],
 [0x19e18,0x7c2],[0x19f38,0x7c3],[0x1a058,0x7c4],[0x1a178,0x7c5],
 [0x1a3b8,0x7c6],[0x1a4d8,0x7c7],
].map(([offset,id])=>Object.freeze({offset,id})));

// Spell-specific setup in state27, 4c781..4ca1a. Texture/font preparation and
// the following profile/text refresh helpers belong to their respective owners.
export function initializeSpellMenuAnimations(group,resources,{disabled=new Uint8Array(173)}={}){
 initializeSelectionAnimations(group,resources,{disabled});
 const resource=resources.get(spellMenuAsset.file);if(!resource)throw Error('TH06nc: missing spell menu ANM');
 group.bank.load(resource,spellMenuAsset.base,{slot:spellMenuAsset.slot});
 for(const {offset,id}of spellMenuVmSlots){
  const vm=group.bank.createVm(id);vm.tick();vm.v.setUint16(0x36,vm.v.getUint16(0x34,true),true);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|0x2008,true);vm.v.setUint32(0xec,0xffffffff,true);group.slots.set(offset,vm);
 }
 const sprite=new AnmVm({scripts:[],sprites:[]},0,{allowMissing:true,resolveSprite:id=>group.bank.sprites.get(id)});sprite.bindSprite(0x7cc);
 // This is 1da0 + direct sprite binding 2980, not script initializer 2760.
 sprite.v.setInt32(0xb4,-1,true);sprite.v.setUint16(0x108,0,true);
 for(const p of [0xc8,0xcc,0xd0])sprite.v.setFloat32(p,0,true);
 for(const p of [0xe4,0xe8])sprite.v.setFloat32(p,0.550000011920929,true);
 sprite.v.setUint32(0xc4,(sprite.v.getUint32(0xc4,true)&~0x300)|0x2409,true);sprite.v.setUint32(0xec,0xffffffff,true);group.slots.set(0x1a298,sprite);
 for(const offset of [0x122e0,0x12400,0x12520,0x12640,0x13060,0x13180,0x132a0,0x133c0]){
  const vm=group.slots.get(offset);vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)&~2,true);
 }
}
