import {AnmVm} from './anm-vm.mjs';
// Native loader publishes sprites and scripts at local ID + caller's base.
// Keep independent tables: overlay resources can replace sprites without scripts.
export class AnmBank {
 constructor(){this.sprites=new Map();this.scripts=new Map();this.slots=new Map();}
 load(resource,base,{slot=null}={}){
  if(!Number.isInteger(base)||base<0||base>32767)throw Error('TH06nc ANM: invalid resource base');
  if(slot!==null){this.unload(slot);this.slots.set(slot,{resource,base});}
  for(const sprite of resource.sprites){
   const binding=this.sprites.get(sprite.id+base)??{};
   Object.assign(binding,{resource,sprite,active:true});this.sprites.set(sprite.id+base,binding);
  }
  for(const script of resource.scripts)this.scripts.set(script.id+base,{resource,script,base});
 }
 unload(slot){
  const entry=this.slots.get(slot);if(!entry)return;
  for(const s of entry.resource.sprites){const b=this.sprites.get(s.id+entry.base);if(b)Object.assign(b,{active:false,sprite:null,resource:null});}
  for(const s of entry.resource.scripts)this.scripts.delete(s.id+entry.base);
  this.slots.delete(slot);
 }
 createVm(id,options={}){
  const binding=this.scripts.get(id);
  if(!binding){
   if(options.allowMissing)return new AnmVm({scripts:[],sprites:[]},id,options);
   throw Error(`TH06nc ANM: missing global script ${id}`);
  }
  const vm=new AnmVm(binding.resource,binding.script.id,{...options,spriteBase:binding.base,resolveSprite:id=>this.sprites.get(id)});
  vm.v.setUint16(0x38,id,true);return vm;
 }
}
