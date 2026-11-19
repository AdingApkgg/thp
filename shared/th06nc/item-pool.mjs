import {rebindAnm} from './anm-rebind.mjs';
import {advanceItemMotion} from './item-motion.mjs';
import {collectItem} from './item-collect.mjs';
const F=Math.fround;
export const itemSlots=1024,itemSlotBytes=0x160;
// Original drop helper 426e0. Ordinary drops, death drops and score points share
// the same pool. Native mode: 0 ordinary, 1 auto-collect, 2 death scatter.
export class ItemPool {
 constructor({anmBank,environment={}}={}){this.anmBank=anmBank;this.environment=environment;this.storage=new Uint8Array(1025*itemSlotBytes);this.entries=new Array(1025);this.cursor=0;this.activeCount=0;}
 entry(slot){if(!this.entries[slot]){const bytes=this.storage.subarray(slot*itemSlotBytes,(slot+1)*itemSlotBytes);this.entries[slot]={slot,bytes,v:new DataView(bytes.buffer,bytes.byteOffset,bytes.byteLength),vm:null};}return this.entries[slot];}
 spawn({type,position,mode,critical=false}){
  mode??=critical?1:0;type|=0;mode|=0;
  if(type<0||type>6||mode<0||mode>2)throw Error('TH06nc: invalid item type/mode');
  const env=this.environment;if(env.spellPractice&&mode!==2&&type!==6)return null;
  let item=this.entry(this.cursor),scanned=0;
  while(true){this.cursor++;if(this.cursor>=itemSlots)this.cursor=0;if(item.v.getUint8(0)===0)break;if(++scanned>=itemSlots)return null;item=this.entry(this.cursor);}
  const {v,bytes}=item;v.setUint8(0,1);position.forEach((x,k)=>v.setFloat32(0x10+k*4,F(x),true));
  if(mode===0){const x=v.getFloat32(0x10,true);if(F(8)>x)v.setFloat32(0x10,8,true);else if(x>F(376))v.setFloat32(0x10,376,true);}
  v.setInt32(0x1c,0,true);v.setFloat32(0x20,F(-2.2),true);v.setInt32(0x24,0,true);v.setUint8(0x34,type);v.setUint8(0xc,mode);v.setInt32(8,0,true);v.setInt32(4,-999,true);
  if(mode===2){if(!env.rng)throw Error('TH06nc: death item scatter requires RNG');v.setFloat32(0x28,F(F(env.rng.float01()*F(288))+F(48)),true);v.setFloat32(0x2c,F(F(env.rng.float01()*F(192))-F(64)),true);v.setInt32(0x30,0,true);for(let k=0;k<3;k++)v.setUint32(0x1c+k*4,v.getUint32(0x10+k*4,true),true);}
  item.vm=rebindAnm(this.anmBank,0x215+type,bytes.subarray(0x38,0x158),{randomU16:env.rng?()=>env.rng.next16():null});v.setUint32(0x124,0xffffffff,true);v.setUint8(0x158,1);return item;
 }
 spawnPoint(request){return this.spawn({...request,type:6,mode:1});}
 // Owner 42980; items run before bullet motion at priority 11.
 tick({player,popups,cancelBullets,soundSlots=[-1,-1,-1],soundDisabled=false,sin=Math.sin,cos=Math.cos,atan2=Math.atan2}={}){
  if(!player)throw Error('TH06nc: item update needs player');
  const position=player.position,state=player.state,lower=player.v?Array.from({length:2},(_,k)=>player.v.getFloat32(0xa29c+k*4,true)):position.map((x,k)=>F(x-F((player.querySize??[12,12])[k]*.5))),upper=player.v?Array.from({length:2},(_,k)=>player.v.getFloat32(0xa2a8+k*4,true)):position.map((x,k)=>F(x+F((player.querySize??[12,12])[k]*.5)));
  this.activeCount=0;let collected=false,pointValue=0;
  for(let slot=0;slot<itemSlots;slot++){
   if(!this.storage[slot*itemSlotBytes])continue;this.activeCount++;const item=this.entry(slot),{v}=item;
   if(!advanceItemMotion(item,{playerPosition:position,playerState:state,sin,cos,atan2}))continue;
   const x=v.getFloat32(0x10,true),y=v.getFloat32(0x14,true);
   if((state===0||state===3)&&!(lower[0]>F(x+8)||F(x-8)>upper[0]||lower[1]>F(y+8)||F(y-8)>upper[1])){
    pointValue=collectItem(item,{environment:this.environment,popups,cancelBullets,soundSlots,soundDisabled,pointValue});collected=true;continue;
   }
   const clock=v.getInt32(8,true);v.setInt32(4,clock,true);v.setInt32(8,(clock+1)|0,true);if(!item.vm)throw Error('TH06nc: active item ANM missing');item.vm.tick();
  }
  if(collected&&!soundDisabled){for(let k=0;k<3;k++){if(soundSlots[k]===21)break;if(soundSlots[k]<0){soundSlots[k]=21;break;}}}
  return this.activeCount;
 }
}
