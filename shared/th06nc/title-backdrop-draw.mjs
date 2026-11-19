// Base-resource-present title draw branch 0x14005499e..0x140054bcc.
// Overlay title00 is drawn later by the owner, after intervening menu layers.
const F=Math.fround;
export function drawTitleBackdropBase(group,draw,{addColor=[0,0,0]}={}){
 const vm=p=>group.slots.get(p),alpha=v=>v.v.getUint8(0xef);
 const base=vm(0x16170);if(alpha(base))draw(base,{snap:true,addColor});
 const scaled=vm(0x163b0);
 if(alpha(scaled)){
  const v=scaled.v,original=v.getUint32(0xe8,true);
  const ratio=F(F(v.getFloat32(0xe4,true)-F(0.6075))/F(0.13365));
  const t=Math.max(0,Math.min(1,ratio)),factor=F(F(t*F(0.11475408))+1);
  v.setFloat32(0xe8,F(factor*v.getFloat32(0xe8,true)),true);
  try{draw(scaled,{snap:false,addColor});}finally{v.setUint32(0xe8,original,true);}
 }
 const tinted=vm(0x164d0);
 if(alpha(tinted)){
  const control=vm(0x16710).v.getUint32(0xec,true),a=control>>>24;
  const tint=[16,8,0].map(shift=>Math.floor((((control>>>shift)&255)*a+127)/255));
  const original=tinted.v.getUint32(0xec,true),white=255-a;
  tinted.v.setUint32(0xec,(original&0xff000000)|(white<<16)|(white<<8)|white,true);
  try{draw(tinted,{snap:false,addColor:tint});}finally{tinted.v.setUint32(0xec,original,true);}
 }
 const foreground=vm(0x165f0);if(alpha(foreground))draw(foreground,{snap:false,addColor});
}
