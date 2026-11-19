import {rebindAnm} from './anm-rebind.mjs';
const F=Math.fround;
// Original query helper 69d00: active shots plus 32 bomb damage rectangles.
export function queryPlayerDamage(player,{position,size},{spawnEffect=null}={}){
 const {bytes,v,anms,anmBank,environment={}}=player,hx=F(F(size[0])*F(0.5)),hy=F(F(size[1])*F(0.5)),left=F(F(position[0])-hx),right=F(F(position[0])+hx),top=F(F(position[1])-hy),bottom=F(F(position[1])+hy);let damage=0,critical=false;
 const intersects=(x,y,w,h)=>{const a=F(F(w)*F(0.5)),b=F(F(h)*F(0.5));return !(F(F(y)-b)>bottom||F(F(x)-a)>right||top>F(b+F(y))||left>F(a+F(x)));};
 const effect=(type,p)=>{if(!spawnEffect)throw Error('TH06nc: shot impact effect service missing');spawnEffect({type,count:1,color:0xffffffff,position:p});};
 for(let slot=0;slot<80;slot++){
  const base=0x410+slot*0x170,d=new DataView(bytes.buffer,bytes.byteOffset+base,0x170),state=d.getUint16(0x10,true),kind=d.getInt16(0x12,true);if(!state||(state!==1&&kind!==2))continue;
  const f=p=>d.getFloat32(p,true),sf=(p,x)=>d.setFloat32(p,F(x),true),shotPosition=()=>[f(0x13c),f(0x140),f(0x144)];
  if(!intersects(f(0x13c),f(0x140),f(0x160),f(0x164)))continue;
  const amount=d.getInt16(0x15c,true);damage=(damage+(v.getUint8(0x9ec8)?Math.trunc(amount/3)||1:amount))|0;
  if(kind===2){
   d.setInt16(0x15c,Math.trunc(amount/4)||1,true);const script=d.getInt16(0x50,true),extent=script===0x461?32:script===0x462?42:script===0x463||script===0x464?48:null;if(extent!==null){sf(0x160,extent);sf(0x164,extent);}
   if(d.getInt32(4,true)%6===0)effect(5,shotPosition());
  }
  if(kind!==3){
   if(state===1){const script=d.getInt16(0x50,true)+32,offset=base+0x18;anms.set(offset,rebindAnm(anmBank,script,bytes.subarray(offset,offset+288),{randomU16:environment.rng?()=>environment.rng.next16():null}));effect(5,shotPosition());sf(0x144,0.1);}
   d.setUint16(0x10,2,true);sf(8,F(f(8)*F(0.125)));sf(0xc,F(f(0xc)*F(0.125)));
  }else{const counter=(v.getUint8(0x7718)+1)&255;v.setUint8(0x7718,counter);if((counter&7)===0)effect(5,[f(0x13c),F(position[1]),F(position[2])]);}
 }
 for(let index=0;index<32;index++){
  const p=index*12,width=v.getFloat32(0x180+p,true);if(!(width>0)||!intersects(v.getFloat32(p,true),v.getFloat32(p+4,true),width,v.getFloat32(0x184+p,true)))continue;
  const amount=v.getInt32(0x300+index*4,true);damage=(damage+amount)|0;v.setInt32(0x380+index*4,v.getInt32(0x380+index*4,true)+amount,true);const counter=(v.getUint8(0x7718)+1)&255;v.setUint8(0x7718,counter);if((counter&3)===0)effect(3,position.map(F));if(v.getUint8(0x9ec8))critical=true;
 }
 return {damage,critical};
}
