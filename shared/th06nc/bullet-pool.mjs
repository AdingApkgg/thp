import {rebindAnm} from './anm-rebind.mjs';
import {spriteLogicalSize} from './sprite-layout.mjs';
import {bulletPattern} from './bullet-pattern.mjs';
import {advanceBullet} from './bullet-update.mjs';
const F=Math.fround;
const scripts=[[512,526,527,528,523],[513,529,530,531,524],[514,529,530,531,524],[515,529,530,531,524],[516,529,530,531,524],[517,529,530,531,524],[518,532,532,532,525],[519,532,532,532,525],[520,532,532,532,525],[698,700,700,700,699]];
const smallColors=[0,1,1,1,1,2,2,2,2,3,3,3,4,4,4,0],mediumColors=[0,1,1,2,2,3,4,0];
export const bulletSlots=640,bulletSlotBytes=0x620;
// Original f870 constructor. Movement is intentionally a separate manager step.
export class BulletPool {
 constructor({anmBank,environment={},sin=Math.sin,cos=Math.cos,atan2=Math.atan2,soundSlots=null,soundDisabled=false}={}){
  this.anmBank=anmBank;this.environment=environment;this.sin=sin;this.cos=cos;this.atan2=atan2;this.soundSlots=soundSlots;this.soundDisabled=soundDisabled;
  this.storage=new Uint8Array(bulletSlots*bulletSlotBytes);this.entries=new Array(bulletSlots);this.cursor=0;
  this.templates=scripts.map(ids=>{
   const bytes=new Uint8Array(0x5b0),v=new DataView(bytes.buffer),anms=ids.map((id,i)=>rebindAnm(anmBank,id,bytes.subarray(i*0x120,(i+1)*0x120),{randomU16:environment.rng?()=>environment.rng.next16():null}));
   v.setUint16(0x36,v.getUint16(0x34,true),true);const size=spriteLogicalSize(anms[0].boundSprite)[0];v.setUint8(0x5a0,Math.trunc(size));
   const radius=size<=8?4:size<=16?([514,517].includes(ids[0])?4:ids[0]===516?5:6):size<=32?(ids[0]===519?11:ids[0]===520?9:16):32;
   v.setFloat32(0x5a4,radius,true);v.setFloat32(0x5a8,radius,true);return {bytes,anms};
  });
 }
 entry(slot){if(!this.entries[slot]){const bytes=this.storage.subarray(slot*bulletSlotBytes,(slot+1)*bulletSlotBytes);this.entries[slot]={slot,bytes,v:new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),anms:new Array(5)};}return this.entries[slot];}
 copyAnm(entry,index,template){
  const state=entry.bytes.subarray(0x50+index*0x120,0x50+(index+1)*0x120);state.set(template.bytes.subarray(index*0x120,(index+1)*0x120));
  const id=new DataView(state.buffer,state.byteOffset,state.byteLength).getUint16(0x38,true),vm=this.anmBank.createVm(id,{allowMissing:true,randomU16:this.environment.rng?()=>this.environment.rng.next16():null});vm.state=state;vm.v=new DataView(state.buffer,state.byteOffset,state.byteLength);vm.boundBinding=this.anmBank.sprites.get(vm.pointer(0x100)-1);entry.anms[index]=vm;return vm;
 }
 spawn(descriptor){
  const env=this.environment;if(env.spellPractice&&env.spellFinished)return [];
  const d=new DataView(descriptor.buffer,descriptor.byteOffset,descriptor.byteLength),ways=d.getInt16(0x18,true),layers=d.getInt16(0x1a,true),type=d.getInt16(0x2c,true),color=d.getInt16(0x2e,true),flags=d.getUint16(0,true),template=this.templates[type];
  if(!template)throw Error('TH06nc: invalid bullet type '+type);
  const player=env.playerPosition??[0,0,0],dx=F(F(player[0])-d.getFloat32(0xc,true)),dy=F(F(player[1])-d.getFloat32(0x10,true)),aim=dx===0&&dy===0?F(Math.PI/2):F(this.atan2(dy,dx)),spawned=[];
  let exhausted=false;
  for(let layer=0;layer<layers&&!exhausted;layer++)for(let way=0;way<ways;way++){
   let entry=this.entry(this.cursor),searched=0;
   while(true){this.cursor++;if(this.cursor>=bulletSlots)this.cursor=0;if(entry.v.getUint16(0x44,true)===0)break;if(++searched>=bulletSlots){exhausted=true;break;}entry=this.entry(this.cursor);}
   if(exhausted)break;
   const {v,bytes}=entry,{angle,speed,rawAngle}=bulletPattern(descriptor,way,layer,{aim,rng:env.rng});
   v.setFloat32(0x24,speed,true);v.setUint16(0x44,1,true);v.setFloat32(0x40,angle,true);v.setUint32(0x30,d.getUint32(0xc,true),true);v.setUint32(0x34,d.getUint32(0x10,true),true);v.setFloat32(0x38,F(0.1),true);v.setFloat32(8,F(F(this.cos(angle))*speed),true);v.setFloat32(0xc,F(F(this.sin(angle))*speed),true);v.setUint16(0x14,flags,true);v.setUint16(0x3c,color,true);
   const main=this.copyAnm(entry,0,template),cancel=this.copyAnm(entry,4,template),tv=new DataView(template.bytes.buffer);bytes.set(template.bytes.subarray(0x5a4,0x5b0),0x5f4);v.setUint8(0x5f0,tv.getUint8(0x5a0));
   const palette=id=>{const size=spriteLogicalSize(main.boundSprite)[0];if(size<=16){if(smallColors[color]===undefined)throw Error('TH06nc: invalid small bullet color');return id+smallColors[color];}if(size<=32){if(v.getUint16(0x88,true)===519)return id+1;if(mediumColors[color]===undefined)throw Error('TH06nc: invalid medium bullet color');return id+mediumColors[color];}return id+color;};
   for(const [mask,index,state]of [[2,1,2],[4,2,3],[8,3,4]])if(flags&mask){const vm=this.copyAnm(entry,index,template);vm.bindSprite(palette(vm.v.getInt16(0x34,true)));v.setUint16(0x44,state,true);break;}
   main.bindSprite(main.v.getInt16(0x34,true)+color);cancel.bindSprite(palette(cancel.v.getInt16(0x34,true)));
   if(flags&0x10){const direction=d.getFloat32(0x44,true),accel=d.getFloat32(0x40,true),a=direction<=-999?rawAngle:direction;v.setFloat32(0x608,F(F(this.cos(a))*accel),true);v.setFloat32(0x60c,F(F(this.sin(a))*accel),true);const duration=d.getInt32(0x1c,true);v.setInt32(0x48,duration>0?duration:99999,true);v.setInt32(0x610,0,true);}
   else if(flags&0x20){v.setUint32(0x600,d.getUint32(0x40,true),true);v.setUint32(0x18,d.getUint32(0x44,true),true);v.setUint32(0x48,d.getUint32(0x1c,true),true);}
   if(flags&0x1c0){v.setUint32(0x614,d.getUint32(0x40,true),true);const s=d.getFloat32(0x44,true);v.setFloat32(0,s<0?speed:s,true);v.setUint32(4,d.getUint32(0x1c,true),true);v.setUint32(0x20,d.getUint32(0x20,true),true);v.setInt32(0x1c,0,true);}
   if(flags&0xc00){const s=d.getFloat32(0x40,true);v.setFloat32(0,s<0?speed:s,true);v.setUint32(0x20,d.getUint32(0x1c,true),true);v.setInt32(0x1c,0,true);}
   spawned.push(entry);
  }
  if(flags&0x200&&!this.soundDisabled&&this.soundSlots){const sound=d.getInt32(0x3c,true);if(!this.soundSlots.includes(sound)){const index=this.soundSlots.findIndex(x=>x<0);if(index>=0)this.soundSlots[index]=sound;}}
  return spawned;
 }
 tick(options={}){this.activeCount=0;for(let slot=0;slot<bulletSlots;slot++){const entry=this.entry(slot);if(entry.v.getUint16(0x44,true)){this.activeCount++;advanceBullet(entry,{environment:this.environment,sin:this.sin,cos:this.cos,atan2:this.atan2,soundSlots:this.soundSlots??[-1,-1,-1],soundDisabled:this.soundDisabled,...options});}}return this.activeCount;}
}
