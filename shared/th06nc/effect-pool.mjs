import {rebindAnm} from './anm-rebind.mjs';
import {advanceEffectCallback} from './effect-update.mjs';
export const effectBytes=0x198;
// Original 21-entry effect table at 3de1b0, script ID and callback address.
export const effectKinds=Object.freeze([[701,0],[702,0],[703,0],[704,0x14002a830],[707,0x14002a620],[708,0x14002a620],[709,0x14002a620],[710,0x14002a620],[711,0x14002a620],[712,0x14002a620],[713,0x14002a620],[714,0x14002a620],[715,0],[716,0x14002aae0],[716,0x14002aae0],[716,0x14002aae0],[723,0],[705,0x14002ae30],[706,0x14002af80],[717,0x14002aa50],[719,0x14002a410]].map(Object.freeze));
// Spawn helper 2b0d0. The extra slot is the original exhausted-pool sentinel.
export class EffectPool {
 constructor({anmBank,rng=null,sin=Math.sin,cos=Math.cos}={}){this.anmBank=anmBank;this.rng=rng;this.sin=sin;this.cos=cos;this.storage=new Uint8Array(513*effectBytes);this.entries=new Array(513);this.cursor=0;this.activeCount=0;}
 entry(slot){
  if(!this.entries[slot]){const bytes=this.storage.subarray(slot*effectBytes,(slot+1)*effectBytes);this.entries[slot]={slot,pointer:BigInt(slot+1),bytes,v:new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),vm:null};}
  return this.entries[slot];
 }
 spawn({type,position,count=1,color=0xffffffff}){
  const definition=effectKinds[type];if(!definition)throw Error('TH06nc: unknown effect type');
  count|=0;
  for(let scanned=0;scanned<512;scanned++){
   const slot=this.cursor;this.cursor=(this.cursor+1)%512;
   const effect=this.entry(slot),{v,bytes}=effect;if(v.getUint8(0x14))continue;
   v.setUint8(0x14,1);v.setUint8(0x170,type&255);for(let i=0;i<3;i++)v.setFloat32(0x174+i*4,position[i],true);
   effect.vm=rebindAnm(this.anmBank,definition[0],bytes.subarray(0x40,0x160),{randomU16:this.rng?()=>this.rng.next16():null});
   v.setUint32(0x12c,color>>>0,true);v.setBigUint64(0,BigInt(definition[1]),true);v.setInt32(0x28,0,true);v.setInt32(0x24,-999,true);v.setUint8(0x180,0);v.setUint8(0x3c,0);
   count=(count-1)|0;if(count===0)return effect;
  }
  return this.entry(512);
 }
 tick(){
  this.activeCount=0;
  for(let slot=0;slot<512;slot++){
   const effect=this.entry(slot),{v}=effect;if(!v.getUint8(0x14))continue;this.activeCount++;
   if(advanceEffectCallback(effect,{rng:this.rng,sin:this.sin,cos:this.cos})!==1)v.setUint8(0x14,0);
   if(!effect.vm)throw Error('TH06nc: active effect animation binding missing');
   if(effect.vm.tick()!==0)v.setUint8(0x14,0);
   const frame=v.getInt32(0x28,true);v.setInt32(0x24,frame,true);v.setInt32(0x28,(frame+1)|0,true);
  }
  return this.activeCount;
 }
}
