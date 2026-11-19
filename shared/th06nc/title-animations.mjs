import {AnmBank} from './anm-bank.mjs';
import {titleResources,titleVmSlots} from './title-layout.mjs';
import {updateTitleMenuItem} from './title-menu-item.mjs';
// Resource and VM initialization only. Title owner input/state/draw order is
// deliberately kept outside this class until reconstructed from its native code.
export class TitleAnimations {
 constructor(resources,{disabled=new Uint8Array(0x7d),randomU16=null}={}){
  this.bank=new AnmBank();
  for(const ref of titleResources){const resource=resources.get(ref.file);if(!resource)throw Error(`TH06nc: missing title resource ${ref.file}`);this.bank.load(resource,ref.base,{slot:ref.slot});}
  this.slots=new Map();
  for(const slot of titleVmSlots(disabled)){
   const vm=this.bank.createVm(slot.id,{allowMissing:true,randomU16});
   // Native 0x140002760 runs time-zero instructions immediately; the wrapper
   // then retains sprite ID and sets bit 13 (0x140046dc0 / inlined variants).
   vm.tick();vm.v.setUint16(0x36,vm.v.getUint16(0x34,true),true);
   vm.v.setUint32(0xc4,vm.v.getUint32(0xc4,true)|0x2000,true);
   this.slots.set(slot.offset,vm);
  }
 }
 presentItem(offset,selection){
  const vm=this.slots.get(offset);if(!vm)throw Error(`TH06nc: missing title item slot ${offset}`);
  updateTitleMenuItem(vm,selection);return vm;
 }
}
