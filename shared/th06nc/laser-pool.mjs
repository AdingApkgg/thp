import {rebindAnm} from './anm-rebind.mjs';
import {advanceLaser} from './laser-update.mjs';
import {drawLasers} from './laser-draw.mjs';
export const laserSlotBytes=0x298,laserSlots=64;
const endColors=Object.freeze([0,1,1,1,1,2,2,2,2,3,3,3,4,4,4,0]),F=Math.fround;
// Native laser creation helper 105e0..10860; one extra exhausted-pool slot.
export class LaserPool {
 constructor({anmBank,environment={},atan2=Math.atan2}={}){this.anmBank=anmBank;this.environment=environment;this.atan2=atan2;this.storage=new Uint8Array(65*laserSlotBytes);this.entries=new Array(65);}
 entry(slot){if(!this.entries[slot]){const bytes=this.storage.subarray(slot*laserSlotBytes,(slot+1)*laserSlotBytes);this.entries[slot]={slot,pointer:BigInt(slot+1),bytes,v:new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),main:null,end:null};}return this.entries[slot];}
 spawn(descriptor){
  const env=this.environment;if(env.spellPractice&&env.spellFinished)return null;
  const d=new DataView(descriptor.buffer,descriptor.byteOffset,descriptor.byteLength);let slot=0;while(slot<64&&this.entry(slot).v.getUint8(0x274))slot++;const laser=this.entry(slot);if(slot===64)return laser;
  const {v,bytes}=laser,type=d.getInt16(0xc,true),color=d.getInt16(0xe,true);if(color<0||color>=16)throw Error('TH06nc: invalid laser color');
  const options={randomU16:env.rng?()=>env.rng.next16():null};
  laser.main=rebindAnm(this.anmBank,0x29a+type,bytes.subarray(0x20,0x140),options);laser.main.bindSprite(v.getInt16(0x54,true)+color);
  laser.end=rebindAnm(this.anmBank,0x21c,bytes.subarray(0x140,0x260),options);laser.end.bindSprite(v.getInt16(0x174,true)+endColors[color]);v.setUint32(0x204,v.getUint32(0x204,true)|4,true);
  for(let i=0;i<3;i++)v.setUint32(0x278+i*4,d.getUint32(0x20+i*4,true),true);v.setUint16(0x284,d.getUint16(0xe,true),true);v.setUint8(0x274,1);
  let angle=d.getFloat32(0x3c,true);
  if(d.getUint8(0x2c)===0){const player=env.playerPosition??[0,0,0],dx=F(F(player[0])-d.getFloat32(0x20,true)),dy=F(F(player[1])-d.getFloat32(0x24,true));angle=F(angle+(dx===0&&dy===0?F(Math.PI/2):F(this.atan2(dy,dx))));}
  v.setFloat32(0x260,angle,true);v.setUint16(0x264,d.getUint16(0x14,true),true);v.setInt32(0xc,0,true);v.setInt32(8,-999,true);
  for(const [target,source]of [[0x10,0x18],[0x14,0x1c],[0x288,0x40],[4,0x10],[0x26c,8],[0x270,0x30],[0x268,0x34],[0x18,0x38],[0x28c,0],[0,4]])v.setUint32(target,d.getUint32(source,true),true);
  v.setUint8(0x290,d.getInt32(0x30,true)===0?1:0);return laser;
 }
 tick(options={}){let active=0;for(let slot=0;slot<64;slot++){const laser=this.entry(slot);if(laser.v.getUint8(0x274)){active++;advanceLaser(laser,options);}}return active;}
 draw(draw,options){drawLasers(this,draw,options);}
}
